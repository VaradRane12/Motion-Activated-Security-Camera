import os
import boto3
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

app = Flask(__name__)

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
    return render_template("index.html", videos=videos)

@app.route("/live_feed")
def live_feed():
    # Implement your live feed logic here
    return jsonify({"status": "Live feed activated", "message": "Connecting to live stream..."})

@app.route("/shutdown", methods=["POST"])
def shutdown():
    # Implement shutdown logic here
    print("Shutdown requested")
    return jsonify({"status": "Shutdown initiated", "message": "System shutting down safely..."})

@app.route("/arm_light", methods=["POST"])
def arm_light():
    # Implement light arming logic here 
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
    # Implement siren arming logic here
    print("Siren armed")
    return jsonify({"status": "Siren armed", "message": "Motion detection siren activated"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
