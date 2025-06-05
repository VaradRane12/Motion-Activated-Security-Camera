import cv2
import time
from datetime import datetime
import numpy as np
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from libcamera import Transform
import boto3
picam2 = Picamera2()
s3_client = boto3.client("s3")

# Configuration for motion detection
motion_config = picam2.create_video_configuration(
    lores={"size": (320, 240), "format": "YUV420"},
    main={"size": (640, 480), "format": "RGB888"},
    transform=Transform(hflip=1, vflip=1),
    controls={"FrameRate": 15}
)

# Configuration for recording (higher res, no lores needed)
record_config = picam2.create_video_configuration(
    main={"size": (1920, 1080), "format": "RGB888"},
    transform=Transform(hflip=1, vflip=1),
    controls={"FrameRate": 15}
)

picam2.configure(motion_config)
picam2.start()
time.sleep(2)

encoder = H264Encoder()

last_frame = None
recording = False
record_duration = 20
cooldown_after_recording = 3
last_motion_time = 0
motion_threshold_area = 1000

while True:
    # Motion detection stream
    yuv_buffer = picam2.capture_buffer("lores")
    yuv = np.frombuffer(yuv_buffer, dtype=np.uint8)
    yuv = yuv.reshape((240 * 3 // 2, 320))  # YUV420 = 1.5 bytes per pixel
    frame = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    current_time = time.time()

    if last_frame is None:
        last_frame = gray
        continue

    frame_delta = cv2.absdiff(last_frame, gray)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = any(cv2.contourArea(c) > motion_threshold_area for c in contours)

    if motion_detected and (current_time - last_motion_time) > cooldown_after_recording:
        print("Motion detected. Starting recording...")
        timestamp = datetime.now().strftime("%y%b%d_%H-%M-%S")
        h264_path = f"/home/pi/Desktop/{timestamp}.h264"
        output = FileOutput(h264_path)

        # Stop motion detection stream
        picam2.stop()
        time.sleep(1)  # Let camera reset

        # Switch to recording config
        picam2.configure(record_config)
        picam2.start()
        time.sleep(1)
        print("Starting recording...")
        picam2.start_recording(encoder, output)
        start_time = time.time()

        while time.time() - start_time < record_duration:
            print(f"Recording... {int(time.time() - start_time)}s", end='\r')
            time.sleep(1)

        picam2.stop_recording()
        print("Recording done.")


        import subprocess

        mp4_path = h264_path.replace(".h264", ".mp4")

        # Convert .h264 to .mp4 using ffmpeg
        subprocess.run([
            "ffmpeg", "-y", "-r", "15", "-i", h264_path, "-c:v", "copy", mp4_path
        ], check=True)


        print(f"Conversion done: {mp4_path}")


        # Upload to S3
        bucket_name = "motion-camera-storage"
        s3_key = f"motion_videos/{timestamp}.mp4"

        try:
            s3_client.upload_file(mp4_path, bucket_name, s3_key)
            print(f"Uploaded to S3: s3://{bucket_name}/{s3_key}")
        except Exception as e:
            print(f"Failed to upload to S3: {e}")


        # Reset to motion detection stream
        picam2.stop()
        time.sleep(1)
        picam2.configure(motion_config)
        picam2.start()
        time.sleep(1)

        last_frame = None
        last_motion_time = time.time()

    else:
        last_frame = gray

    time.sleep(0.1)
