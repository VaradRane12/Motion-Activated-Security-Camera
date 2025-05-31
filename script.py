import cv2
import time
from datetime import datetime
import numpy as np
import os
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from libcamera import Transform
import boto3

picam2 = Picamera2()
s3_client = boto3.client("s3")

# Configurations
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

picam2.configure(motion_config)
picam2.start()
time.sleep(2)

encoder = H264Encoder()

last_frame = None
recording = False
record_duration = 5
cooldown_after_recording = 3
last_motion_time = 0
motion_threshold_area = 1000

while True:
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
        print("🔴 Motion detected. Starting recording...")
        timestamp = datetime.now().strftime("%y%b%d_%H-%M-%S")
        h264_path = f"/home/pi/Desktop/{timestamp}.h264"
        output = FileOutput(h264_path)

        # Stop motion detection
        picam2.stop()
        time.sleep(0.2)
        picam2.configure(record_config)
        picam2.start()
        time.sleep(0.2)

        picam2.start_recording(encoder, output)
        time.sleep(record_duration)
        picam2.stop_recording()
        print("✅ Recording done.")

        # Upload to S3
        bucket_name = "motion-camera-storage"
        s3_key = f"motion_videos/{timestamp}.h264"

        try:
            s3_client.upload_file(h264_path, bucket_name, s3_key)
            print(f"☁️ Uploaded to S3: s3://{bucket_name}/{s3_key}")

            # Clean up older S3 videos (keep latest 16)
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="motion_videos/")
            if 'Contents' in response:
                all_objects = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
                old_objects = all_objects[16:]

                if old_objects:
                    to_delete = [{'Key': obj['Key']} for obj in old_objects]
                    s3_client.delete_objects(Bucket=bucket_name, Delete={'Objects': to_delete})
                    print(f"🗑️ Deleted {len(to_delete)} old videos from S3.")

        except Exception as e:
            print(f"❌ Failed to upload or clean S3: {e}")

        # Delete local file
        if os.path.exists(h264_path):
            os.remove(h264_path)
            print("🧹 Deleted local file.")

        # Reset
        picam2.stop()
        time.sleep(0.2)
        picam2.configure(motion_config)
        picam2.start()
        time.sleep(0.2)

        last_frame = None
        last_motion_time = time.time()
    else:
        last_frame = gray

    time.sleep(0.1)
