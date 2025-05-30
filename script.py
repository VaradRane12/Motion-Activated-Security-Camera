import cv2
import time
from datetime import datetime
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from libcamera import Transform
while True:

    picam2 = Picamera2()
    video_config = picam2.create_video_configuration(
        main={"size": (640, 480)}, transform=Transform(hflip=1, vflip=1))
    picam2.configure(video_config)
    picam2.start()

    encoder = H264Encoder()

    time.sleep(2)
    last_frame = None
    recording = False
    record_start_time = 0
    record_duration = 5  # seconds
    cooldown_after_recording = 3  # seconds
    last_motion_time = 0

    motion_threshold_area = 1000

    print("start")
    print(recording)
    frame = picam2.capture_array()
    print(recording)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    current_time = time.time()
    
    if not recording:
        print("In if")
        if last_frame is None:
            last_frame = gray
            continue

        frame_delta = cv2.absdiff(last_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print("detecting motion")
        motion_detected = any(cv2.contourArea(c) > motion_threshold_area for c in contours)
        print("this is after the motion detection")
        if motion_detected and (current_time - last_motion_time) > cooldown_after_recording:
            print("Motion Detected! Starting recording...")
            timestamp = datetime.now().strftime("%y%b%d_%H-%M-%S")
            h264_path = f"/home/pi/Desktop/{timestamp}.h264"
            output = FileOutput(h264_path)

            picam2.start_recording(encoder, output)
            recording = True
            record_start_time = current_time
            last_motion_time = current_time
        else:
            last_frame = gray  # keep updating baseline frame if no motion
    else:
        # Still recording
        if current_time - record_start_time >= record_duration:
            picam2.stop_recording()
            recording = False
            print("Recording complete.")
            last_frame = None  # Reset frame so it doesn't use old one
    print("out of hte stop recording")

    time.sleep(0.1)
