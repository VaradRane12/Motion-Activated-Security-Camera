from gpiozero import MotionSensor
from picamera2 import Picamera2, Preview
import time
import os

pir = MotionSensor(4)
picam2 = Picamera2()

picam2.configure(picam2.create_video_configuration())
picam2.set_controls({"Rotation": 180})

# Optional: Comment this out if using headless
picam2.start_preview(Preview.QT)

while True:
    pir.wait_for_motion()
    print("Motion detected!")
    
    timestamp = time.strftime("%y%b%d_%H:%M:%S")
    h264_path = f"/home/pi/Desktop/{timestamp}.h264"
    mp4_path = f"/home/pi/Desktop/{timestamp}.mp4"

    picam2.start_recording(h264_path)
    pir.wait_for_no_motion()
    picam2.stop_recording()
    
    # Convert to .mp4 using MP4Box if installed
    os.system(f"MP4Box -add {h264_path} {mp4_path}")
    os.remove(h264_path)
