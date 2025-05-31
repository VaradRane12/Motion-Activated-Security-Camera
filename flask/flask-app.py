import os
import boto3
from flask import Flask, render_template
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

    if 'Contents' in response:
        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith(".mp4"):
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': S3_BUCKET, 'Key': key},
                    ExpiresIn=3600  # 1 hour
                )
                videos.append({'name': key, 'url': presigned_url})
    
    return videos

@app.route("/")
def index():
    videos = get_video_files()
    return render_template("index.html", videos=videos)

if __name__ == "__main__":
    app.run(debug=True)
    