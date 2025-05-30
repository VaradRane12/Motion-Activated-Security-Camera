import cv2
import time
from datetime import datetime
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from libcamera import Transform
import os

# Initialize camera
picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": (640, 480)}, transform=Transform(hflip=1, vflip=1))
picam2.configure(video_config)
picam2.start()

encoder = H264Encoder()

# Frame processing setup
time.sleep(2)
last_frame = None
recording = False
i = 0

# Motion recording cooldown (in seconds)
cooldown = 10
last_motion_time = 0

while True:
    frame = picam2.capture_array()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    
    print("started", i)
    i += 1

    if last_frame is None:
        last_frame = gray
        continue

    # Compute frame difference
    frame_delta = cv2.absdiff(last_frame, gray)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = any(cv2.contourArea(c) > 1000 for c in contours)

    # Optional live preview
    # cv2.imshow("Security Feed", frame)
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break

    # If motion is detected, not already recording, and cooldown passed
    if motion_detected and not recording and (time.time() - last_motion_time > cooldown):
        print("Motion Detected! Starting recording...")

        # Generate file path
        timestamp = datetime.now().strftime("%y%b%d_%H-%M-%S")
        h264_path = f"/home/pi/Desktop/{timestamp}.h264"
        output = FileOutput(h264_path)

        picam2.start_recording(encoder, output)
        recording = True
        last_motion_time = time.time()

        # Record for 5 seconds
        time.sleep(5)

        picam2.stop_recording()
        recording = False
        print("Recording complete.")

    # Update last frame only when no motion
    if not motion_detected:
        last_frame = gray

    time.sleep(0.1)

# cv2.destroyAllWindows()  # If you're using imshow
