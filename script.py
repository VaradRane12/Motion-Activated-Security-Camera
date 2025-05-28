from gpiozero import MotionSensor
from picamera2 import Picamera2, Preview
from picamera2.outputs import FileOutput
from libcamera import Transform
import time
import os

# Initialize PIR sensor
pir = MotionSensor(4)

# Initialize and configure camera with rotation
picam2 = Picamera2()
video_config = picam2.create_video_configuration(transform=Transform(rotation=180))
picam2.configure(video_config)

# Optional: comment this out if headless
picam2.start_preview(Preview.QT)

while True:
    pir.wait_for_motion()
    print("Motion detected!")

    # Format timestamp safely
    timestamp = time.strftime("%y%b%d_%H-%M-%S")
    h264_path = f"/home/pi/Desktop/{timestamp}.h264"
    mp4_path = f"/home/pi/Desktop/{timestamp}.mp4"

    from picamera2.outputs import FileOutput

    file_output = FileOutput(h264_path)
    picam2.start_recording(picam2.encoders, file_output)

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
