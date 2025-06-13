import os
import boto3
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from flask import Response
from picamera2 import Picamera2
import cv2
import time
# Load .env variables
load_dotenv()

app = Flask(__name__)


def generate_frames():
    # Setup Picamera2 only once globally
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
    picam2.start()
    while True:
        # Check if motion is paused (so we don't stream when detection is running)
        if os.path.exists("/home/pi/motion_pause.flag"):
            frame = picam2.capture_array()
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.1)

# Load config from .env
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
S3_PREFIX = os.getenv("S3_PREFIX", "")

# Init boto3 client
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def get_video_files():
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_PREFIX)
    videos = []
    print(response["Contents"][-1])
    
    if 'Contents' in response:
        # First, filter and collect video objects with their metadata
        video_objects = []
        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith(".mp4"):
                video_objects.append(obj)
        
        # Sort video objects by LastModified date (newest first)
        video_objects.sort(key=lambda x: x['LastModified'], reverse=True)
        
        # Generate presigned URLs for sorted videos
        for obj in video_objects:
            key = obj['Key']
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': key},
                ExpiresIn=3600  # 1 hour
            )
            # Extract filename from key for display
            filename = key.split('/')[-1] if '/' in key else key
            videos.append({
                'name': filename,
                'full_key': key,
                'url': presigned_url,
                'last_modified': obj['LastModified'],
                'size': obj['Size']
            })
    
    return videos

@app.route("/")
def index():
    videos = get_video_files()

    pause_flag_path = "/home/pi/motion_pause.flag"
    surveillance_state = "paused" if os.path.exists(pause_flag_path) else "resumed"

    return render_template("index.html", videos=videos, surveillance_state=surveillance_state)

@app.route("/live_feed")
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/shutdown", methods=["POST"])
def shutdown():
    print("Shutdown requested")
    return jsonify({"status": "Shutdown initiated", "message": "System shutting down safely..."})

@app.route("/arm_light", methods=["POST"])
def arm_light():
    print("Light armed")
    return jsonify({"status": "Light armed", "message": "Motion detection light activated"})

@app.route('/pause', methods=['POST'])
def pause_surveillance():
    open("/home/pi/motion_pause.flag", "w").close()
    return '', 204

@app.route('/resume', methods=['POST'])
def resume_surveillance():
    try:
        os.remove("/home/pi/motion_pause.flag")
    except FileNotFoundError:
        pass
    return '', 204

@app.route("/arm_siren", methods=["POST"])
def arm_siren():
    print("Siren armed")
    return jsonify({"status": "Siren armed", "message": "Motion detection siren activated"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
