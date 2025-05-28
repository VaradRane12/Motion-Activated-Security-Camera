from gpiozero import MotionSensor
from picamera2 import Picamera2, Preview
from libcamera import Transform
import time
import os

# Initialize PIR sensor
pir = MotionSensor(4)

# Initialize camera with 180-degree rotation
picam2 = Picamera2()
video_config = picam2.create_video_configuration(transform=Transform(rotation=180))
picam2.configure(video_config)

# Optional: comment this line if running headless
picam2.start_preview(Preview.QT)

# Start main loop
while True:
    pir.wait_for_motion()
    print("Motion detected!")

    # Sanitize timestamp for file name
    timestamp = time.strftime("%y%b%d_%H-%M-%S")
    h264_path = f"/home/pi/Desktop/{timestamp}.h264"
    mp4_path = f"/home/pi/Desktop/{timestamp}.mp4"

    # Start recording
    picam2.start_recording(h264_path)
    pir.wait_for_no_motion()
    picam2.stop_recording()
    print("Motion ended. Recording stopped.")

    # Convert to MP4
    result = os.system(f"MP4Box -add {h264_path} {mp4_path}")
    if result == 0:
        os.remove(h264_path)
        print(f"Saved video: {mp4_path}")
    else:
        print("MP4 conversion failed. Keeping .h264 file.")
