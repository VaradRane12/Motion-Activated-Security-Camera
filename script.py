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
import requests
from dotenv import load_dotenv

PAUSE_FLAG_PATH = "/home/pi/motion_pause.flag"

# PID file
with open("/home/pi/motion_pid", "w") as f:
    f.write(str(os.getpid()))

# Load environment variables for Discord
load_dotenv()
WEBHOOK_INFO = os.getenv("DISCORD_WEBHOOK_INFO")
WEBHOOK_ERROR = os.getenv("DISCORD_WEBHOOK_ERROR")
WEBHOOK_GENERAL = os.getenv("DISCORD_WEBHOOK_GENERAL")

# Discord webhook handler
class DiscordHandler(logging.Handler):
    def __init__(self, webhook_url, level=logging.INFO):
        super().__init__(level)
        self.webhook_url = webhook_url

    def emit(self, record):
        try:
            log_entry = self.format(record)
            payload = {"content": f"**{record.levelname}**: ```{log_entry}```"}
            requests.post(self.webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"Discord logging failed: {e}", file=sys.stderr)

class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO or record.levelno == logging.WARNING

class ErrorFilter(logging.Filter):
    def filter(self, record):
        return record.levelno >= logging.ERROR
    
# Setup logging
# Logging Setup
logger = logging.getLogger("MotionLogger")
logger.setLevel(logging.DEBUG)

log_path = "/home/pi/motion_logs.log"
file_handler = logging.FileHandler(log_path)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

if WEBHOOK_INFO:
    info_handler = DiscordHandler(WEBHOOK_INFO, level=logging.INFO)
    info_handler.addFilter(InfoFilter())
    info_handler.setFormatter(formatter)
    logger.addHandler(info_handler)

if WEBHOOK_ERROR:
    error_handler = DiscordHandler(WEBHOOK_ERROR, level=logging.ERROR)
    error_handler.addFilter(ErrorFilter())
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

# General Logger
logger_general = logging.getLogger("MotionGeneral")
logger_general.setLevel(logging.INFO)

if WEBHOOK_GENERAL:
    general_handler = DiscordHandler(WEBHOOK_GENERAL, level=logging.INFO)
    general_handler.setFormatter(formatter)
    general_handler.addFilter(InfoFilter())  # Optional, filters to INFO/WARNING only
    logger_general.addHandler(general_handler)

def log_general(message):
    if WEBHOOK_GENERAL:
        logger_general.info(message)


# # Redirect stdout/stderr to logger
# class PrintLogger:
#     def write(self, message):
#         if message.strip():
#             logger.info(message.strip())
#     def flush(self):
#         pass

# sys.stdout = PrintLogger()
# sys.stderr = PrintLogger()

# GPIO setup
LED_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.HIGH)

# Cleanup leftover files
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
for file in glob.glob(os.path.join(desktop_path, "*.h264")):
    try:
        os.remove(file)
        print(f"Deleted: {file}")
    except Exception as e:
        print(f"Error deleting {file}: {e}")

def led_Blink(pin):
    try:
        start_time = time.time()
        while time.time() - start_time < 10:
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(0.2)
        GPIO.output(pin, GPIO.HIGH)
    except Exception as e:
        logger.error(f"LED blink failed: {e}")

picam2 = Picamera2()
s3_client = boto3.client("s3")

motion_config = picam2.create_video_configuration(
    lores={"size": (320, 240), "format": "YUV420"},
    main={"size": (640, 480), "format": "RGB888"},
    transform=Transform(hflip=1, vflip=1),
    controls={"FrameRate": 15}
)

record_config = picam2.create_video_configuration(
    main={"size": (640, 480), "format": "RGB888"},
    transform=Transform(hflip=1, vflip=1),
    controls={"FrameRate": 15}
)

def convert_and_upload(h264_path, timestamp):
    bucket_name = "motion-camera-storage"
    try:
        mp4_path = h264_path.replace(".h264", ".mp4")
        subprocess.run(["ffmpeg", "-y", "-r", "15", "-i", h264_path, "-c:v", "copy", mp4_path], check=True)
        print(f"Conversion done: {mp4_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg conversion failed: {e}")
        return

    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="motion_videos/")
        if 'Contents' in response and len(response['Contents']) > 16:
            sorted_files = sorted(response['Contents'], key=lambda x: x['LastModified'])
            for obj in sorted_files[:len(sorted_files) - 15]:
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
                print(f"Deleted: {obj['Key']}")
    except Exception as e:
        logger.warning(f"S3 cleanup failed: {e}")

    try:
        for file in glob.glob("../Desktop/offline_storage/*.mp4"):
            s3_key = f"motion_videos/{os.path.basename(file)}"
            s3_client.upload_file(file, bucket_name, s3_key)
            os.remove(file)
            logger.info(f"Uploaded from offline: {file}")
            print(f"Uploaded from offline: {file}")

        s3_key = f"motion_videos/{timestamp}.mp4"
        s3_client.upload_file(mp4_path, bucket_name, s3_key)
        os.remove(mp4_path)
        logger.info(f"Uploaded: {s3_key}")
        print(f"Uploaded: {s3_key}")
    except Exception as e:
        offline_dir = os.path.join(os.path.expanduser("~"), "Desktop", "offline_storage")
        os.makedirs(offline_dir, exist_ok=True)
        offline_path = os.path.join(offline_dir, f"{timestamp}.mp4")
        shutil.move(mp4_path, offline_path)
        logger.info(f"No Internet: Saved Offline: {s3_key}")

        logger.error(f"Upload failed, saved offline: {offline_path}, Error: {e}")

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
    if os.path.exists(PAUSE_FLAG_PATH):
        print("Motion detection paused.")
        time.sleep(1)
        continue

    yuv_buffer = picam2.capture_buffer("lores")
    yuv = np.frombuffer(yuv_buffer, dtype=np.uint8).reshape((240 * 3 // 2, 320))
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
        threading.Thread(target=led_Blink, args=(LED_PIN,)).start()
        print("Motion detected. Starting recording...")
        log_general("Motion Detected!!!")
        timestamp = datetime.now().strftime("%y%b%d_%H-%M-%S")
        h264_path = f"/home/pi/Desktop/{timestamp}.h264"
        output = FileOutput(h264_path)

        picam2.stop()
        time.sleep(0.025)
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

        threading.Thread(target=convert_and_upload, args=(h264_path, timestamp)).start()

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
