import os
import boto3
import logging
from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from picamera2 import Picamera2
import cv2
import subprocess
import signal
from models import db, Device, ScheduledTask
from discord_logger import DiscordHandler

# Load .env variables
load_dotenv()

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance/lights.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Setup logging
logger = logging.getLogger('flask_app')
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if DISCORD_WEBHOOK_URL:
    discord_handler = DiscordHandler(DISCORD_WEBHOOK_URL, level=logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    discord_handler.setFormatter(formatter)
    logger.addHandler(discord_handler)

# AWS Config
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
S3_PREFIX = os.getenv("S3_PREFIX", "")

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def get_video_files():
    videos = []
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_PREFIX)
        if 'Contents' in response:
            video_objects = [obj for obj in response['Contents'] if obj['Key'].endswith(".mp4")]
            video_objects.sort(key=lambda x: x['LastModified'], reverse=True)

            for obj in video_objects:
                key = obj['Key']
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': S3_BUCKET, 'Key': key},
                    ExpiresIn=3600
                )
                filename = key.split('/')[-1]
                videos.append({
                    'name': filename,
                    'full_key': key,
                    'url': presigned_url,
                    'last_modified': obj['LastModified'],
                    'size': obj['Size']
                })
    except Exception as e:
        logger.error(f"Failed to fetch video files from S3: {e}")
    return videos

MOTION_PID_FILE = "/home/pi/motion_pid"
LIVE_PID_FILE = "/home/pi/live_pid"

def kill_pid_from_file(file):
    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                return True
        except Exception as e:
            logger.error(f"Failed to kill PID from {file}: {e}")
            return False
    return False

picam2 = None

@app.route("/start_live_feed", methods=["POST"])
def start_live_feed():
    kill_pid_from_file(MOTION_PID_FILE)
    return jsonify({'message': 'Surveillance started'})

@app.route('/video_feed')
def video_feed():
    global picam2
    if picam2 is None:
        try:
            picam2 = Picamera2()
            picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
            picam2.start()
        except Exception as e:
            logger.error(f"Failed to start camera feed: {e}")
            return "Camera Error", 500

    def generate_frames():
        while True:
            try:
                frame = picam2.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            except Exception as e:
                logger.error(f"Error in video frame generation: {e}")
                break

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/stop_live_feed", methods=["POST"])
def stop_live_feed():
    global picam2
    try:
        if picam2:
            picam2.stop()
            picam2.close()
            picam2 = None
    except Exception as e:
        logger.error(f"Error stopping camera: {e}")

    try:
        p = subprocess.Popen(["python3", "/home/pi/testing_branches/Motion-Activated-Security-Camera/script.py"])
        with open(MOTION_PID_FILE, "w") as f:
            f.write(str(p.pid))
    except Exception as e:
        logger.error(f"Error starting motion script: {e}")

    return "", 204

@app.route("/")
def index():
    try:
        videos = get_video_files()
    except Exception as e:
        logger.error(f"Error getting videos: {e}")
        videos = []
    pause_flag_path = "/home/pi/motion_pause.flag"
    surveillance_state = "paused" if os.path.exists(pause_flag_path) else "resume"
    device = Device.query.filter_by(name="parking light").first()
    tasks = ScheduledTask.query.all()
    return render_template("index.html", videos=videos, surveillance_state=surveillance_state, device=device, tasks=tasks)

@app.route("/shutdown", methods=["POST"])
def shutdown():
    logger.info("Shutdown requested")
    return jsonify({"status": "Shutdown initiated", "message": "System shutting down safely..."})

@app.route("/arm_light", methods=["POST"])
def arm_light():
    logger.info("Light armed")
    return jsonify({"status": "Light armed", "message": "Motion detection light activated"})

@app.route('/pause', methods=['POST'])
def pause_surveillance():
    try:
        open("/home/pi/motion_pause.flag", "w").close()
    except Exception as e:
        logger.error(f"Failed to pause surveillance: {e}")
    return '', 204

@app.route('/resume', methods=['POST'])
def resume_surveillance():
    try:
        os.remove("/home/pi/motion_pause.flag")
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.error(f"Failed to resume surveillance: {e}")
    return '', 204

@app.route('/light/on', methods=['POST'])
def light_on():
    device = db.session.get(Device, 1)
    try:
        os.system('mosquitto_pub -h localhost -t home/light1 -m "ON"')
        device.status = 'ON'
        db.session.commit()
        return jsonify({'status': 'on'})
    except Exception as e:
        logger.error(f"Failed to turn light on: {e}")
        return jsonify({"status": "failed"})

@app.route('/light/off', methods=['POST'])
def light_off():
    device = db.session.get(Device, 1)
    try:
        os.system('mosquitto_pub -h localhost -t home/light1 -m "OFF"')
        device.status = 'OFF'
        db.session.commit()
        return jsonify({'status': 'off'})
    except Exception as e:
        logger.error(f"Failed to turn light off: {e}")
        return jsonify({"status": "failed"})

@app.route('/add_schedule', methods=['POST'])
def add_schedule():
    time_input = request.form['time']
    action = request.form['action']
    device_name = 'parking light'

    try:
        existing_task = ScheduledTask.query.filter_by(device_name=device_name, action=action).first()
        if existing_task:
            existing_task.time = time_input
            message = "Existing schedule updated"
        else:
            new_task = ScheduledTask(time=time_input, action=action, device_name=device_name)
            db.session.add(new_task)
            message = "New schedule created"
        db.session.commit()
        return jsonify({"status": "Scheduled", "message": message})
    except Exception as e:
        logger.error(f"Failed to add schedule: {e}")
        return jsonify({"status": "failed", "message": str(e)})

@app.route("/arm_siren", methods=["POST"])
def arm_siren():
    logger.info("Siren armed")
    return jsonify({"status": "Siren armed", "message": "Motion detection siren activated"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
