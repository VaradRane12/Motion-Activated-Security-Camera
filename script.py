import cv2
import os
import time
from datetime import datetime
import numpy as np
import subprocess
import threading
import boto3
import RPi.GPIO as GPIO
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from libcamera import Transform



LED_PIN = 17  # BCM numbering (Pin 11)
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.LOW)

def led_Blink(pin):
    try:
        start_time = time.time()
        timeout = 10
        while time.time() < start_time + timeout:

            GPIO.output(LED_PIN, GPIO.HIGH)  # Turn on
            print("LED ON")
            time.sleep(0.2)

            GPIO.output(LED_PIN, GPIO.LOW)   # Turn off
            print("LED OFF")
            time.sleep(0.2)
    except:
        return
# Initialize camera and AWS S3
picam2 = Picamera2()
s3_client = boto3.client("s3")

# Motion detection configuration
motion_config = picam2.create_video_configuration(
    lores={"size": (320, 240), "format": "YUV420"},
    main={"size": (640, 480), "format": "RGB888"},
    transform=Transform(hflip=1, vflip=1),
    controls={"FrameRate": 15}
)

# Recording configuration
record_config = picam2.create_video_configuration(
    main={"size": (1920, 1080), "format": "RGB888"},
    transform=Transform(hflip=1, vflip=1),
    controls={"FrameRate": 15}
)

# Function to handle conversion and S3 upload in a separate thread
import threading

def convert_and_upload(h264_path, timestamp):
    print(f"[THREAD-{threading.get_ident()}] Starting conversion and upload...")
    try:
        mp4_path = h264_path.replace(".h264", ".mp4")

        subprocess.run([
            "ffmpeg", "-y", "-r", "15", "-i", h264_path, "-c:v", "copy", mp4_path
        ], check=True)
        print(f"[THREAD-{threading.get_ident()}] Conversion done: {mp4_path}")

        bucket_name = "motion-camera-storage"
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="motion_videos/")
        print(response["Contents"])
        s3_key = f"motion_videos/{timestamp}.mp4"
        s3_client.upload_file(mp4_path, bucket_name, s3_key)
        os.remove(mp4_path)
        os.remove(h264_path)
        print(f"[THREAD-{threading.get_ident()}] Uploaded to S3: s3://{bucket_name}/{s3_key}")

    except Exception as e:
        print(f"[THREAD-{threading.get_ident()}] Error: {e}")


# Start motion detection
picam2.configure(motion_config)
picam2.start()
time.sleep(2)

encoder = H264Encoder()
last_frame = None
record_duration = 20
cooldown_after_recording = 3
last_motion_time = 0
motion_threshold_area = 1000

while True:
    yuv_buffer = picam2.capture_buffer("lores")
    yuv = np.frombuffer(yuv_buffer, dtype=np.uint8)
    yuv = yuv.reshape((240 * 3 // 2, 320))
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
        led_thread = threading.Thread(target=led_Blink, args=(LED_PIN,))
        led_thread.start()
        print("Motion detected. Starting recording...")
        timestamp = datetime.now().strftime("%y%b%d_%H-%M-%S")
        h264_path = f"/home/pi/Desktop/{timestamp}.h264"
        output = FileOutput(h264_path)

        # Stop motion detection stream
        picam2.stop()
        time.sleep(0.025)

        # Switch to recording config
        picam2.configure(record_config)
        picam2.start()
        time.sleep(0.025)

        picam2.start_recording(encoder, output)
        start_time = time.time()

        while time.time() - start_time < record_duration:
            print(f"Recording... {int(time.time() - start_time)}s", end='\r')
            time.sleep(1)

        picam2.stop_recording()
        print("\nRecording done.")

        # Start the thread for conversion + upload
        upload_thread = threading.Thread(target=convert_and_upload, args=(h264_path, timestamp))
        upload_thread.start()

        # Reset to motion detection stream
        picam2.stop()
        time.sleep(0.025) 
        picam2.configure(motion_config)
        picam2.start()
        time.sleep(0.025)

        last_frame = None
        last_motion_time = time.time()

    else:
        last_frame = gray

    time.sleep(0.1)
