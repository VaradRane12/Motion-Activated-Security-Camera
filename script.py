from gpiozero import MotionSensor
from picamera2 import Picamera2, Preview
import time

pir = MotionSensor(4)
picam2 = Picamera2()

picam2.start_preview(Preview.QTGL)
picam2.set_controls({"Rotation": 180})

while True:
    pir.wait_for_motion()
    print("Motion detected!")
    filename = "/home/pi/Desktop/" + time.strftime("%y%b%d_%H:%M:%S") + ".mp4"
    picam2.start_recording(filename)
    pir.wait_for_no_motion()
    picam2.stop_recording()
