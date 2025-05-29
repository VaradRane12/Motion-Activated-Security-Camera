import cv2
import time
from picamera2 import Picamera2

# Initialize the camera
picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(video_config)
picam2.start()

time.sleep(2)  # Warm-up time

# Initialize motion detection variables
last_frame = None

while True:
    # Get frame from camera
    frame = picam2.capture_array()

    # Convert to grayscale and blur
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # First frame
    if last_frame is None:
        last_frame = gray
        continue

    # Compute difference between frames
    frame_delta = cv2.absdiff(last_frame, gray)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    # Find contours (i.e., motion)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = any(cv2.contourArea(c) > 1000 for c in contours)

    if motion_detected:
        print("Motion Detected!")
        # Add your recording logic here

    last_frame = gray
    time.sleep(0.1)
