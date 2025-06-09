import shutil
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
import glob

import logging
import sys

# Logging setup
logger = logging.getLogger("MotionLogger")
logger.setLevel(logging.DEBUG)

log_path = "/home/pi/motion_logs.log"
file_handler = logging.FileHandler(log_path)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Redirect print and errors to logger
class PrintLogger(object):
    def write(self, message):
        if message.strip():
            logger.info(message.strip())
    def flush(self):
        pass

sys.stdout = PrintLogger()
sys.stderr = PrintLogger()

LED_PIN = 17  # BCM numbering (Pin 11)
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.HIGH)



home_dir = os.path.expanduser("~")
desktop_path = os.path.join(home_dir, "Desktop")

for file in glob.glob(os.path.join(desktop_path, "*.h264")):
    try:
        os.remove(file)
        print(f"Deleted: {file}")
    except Exception as e:
        print(f"Error deleting {file}: {e}")

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
        GPIO.output(LED_PIN, GPIO.HIGH)

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
    main={"size": (640, 480), "format": "RGB888"},
    transform=Transform(hflip=1, vflip=1),
    controls={"FrameRate": 15}
)

# Function to handle conversion and S3 upload in a separate thread
import threading

def convert_and_upload(h264_path, timestamp):
    bucket_name = "motion-camera-storage"
    print(f"[THREAD-{threading.get_ident()}] Starting conversion and upload...")
    try: #try for conversion
        mp4_path = h264_path.replace(".h264", ".mp4")

        subprocess.run([
            "ffmpeg", "-y", "-r", "15", "-i", h264_path, "-c:v", "copy", mp4_path
        ], check=True)
        print(f"[THREAD-{threading.get_ident()}] Conversion done: {mp4_path}")

    except:
        pass  # Replace with logging
        
        #DELETING OLD FILES
    try: #Delete Try
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="motion_videos/")
        if 'Contents' in response and len(response['Contents']) > 16:
            sorted_files = sorted(response['Contents'], key=lambda x: x['LastModified'])
            to_delete = len(sorted_files) - 15
            nuke_list = sorted_files[:to_delete]  # Oldest ones
            for obj in nuke_list:
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
                print(f"Deleted: {obj['Key']}")
    except:
        print("Error in Deleting files on S3")

    else:
        print("No files deleted. Less than or equal to 16 objects present.")
    try:  # uploading previously failed videos
        for file in glob.glob("../Desktop/offline_storage/*.mp4"):
            s3_key = f"motion_videos/{os.path.basename(file)}"
            s3_client.upload_file(file, bucket_name, s3_key)
            os.remove(file)
            print(f"[THREAD-{threading.get_ident()}] Uploaded from offline: s3://{bucket_name}/{s3_key}")

        # uploading the current video
        s3_key = f"motion_videos/{timestamp}.mp4"
        s3_client.upload_file(mp4_path, bucket_name, s3_key)
        os.remove(mp4_path)
        print(f"[THREAD-{threading.get_ident()}] Uploaded to S3: s3://{bucket_name}/{s3_key}")

    except Exception as e:
        home_dir = os.path.expanduser("~")
        offline_dir = os.path.join(home_dir, "Desktop", "offline_storage")
        os.makedirs(offline_dir, exist_ok=True)  # Create folder if missing
        offline_path = os.path.join(offline_dir, f"{timestamp}.mp4")
        shutil.move(mp4_path, offline_path)
        print(f"[THREAD-{threading.get_ident()}] S3 upload failed, stored locally at: {offline_path}")
        print(f"Error: {e}")

    # except Exception as e:
    #     print(f"[THREAD-{threading.get_ident()}] Error: {e}")


# Start motion detection
picam2.configure(motion_config)
picam2.start()
time.sleep(2)

encoder = H264Encoder()
last_frame = None
record_duration = 60
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
