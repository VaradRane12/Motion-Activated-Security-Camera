import os
import time
import schedule
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Load .env for webhook
load_dotenv()
WEBHOOK_LIGHTS = os.getenv("DISCORD_WEBHOOK_GENERAL")

# Setup Flask app and DB
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/pi/Motion-Activated-Security-Camera/flask/instance/lights.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class ScheduledTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(10), default=" ")
    time = db.Column(db.String(5))
    action = db.Column(db.String(20))

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(10), default='OFF')

# Logging to Discord
def log_to_discord(message, is_error=False):
    if not WEBHOOK_LIGHTS:
        return
    try:
        emoji = "❌" if is_error else "💡"
        payload = {
            "content": f"{emoji} {message}"
        }
        requests.post(WEBHOOK_LIGHTS, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send to Discord: {e}")

# Update DB and log
def update_device_status(name, state):
    try:
        with app.app_context():
            device = Device.query.filter_by(name=name).first()
            if not device:
                device = Device(name=name, status=state, last_updated=datetime.utcnow())
                db.session.add(device)
            else:
                device.status = state
                device.last_updated = datetime.utcnow()
            db.session.commit()
            msg = f"Device '{name}' updated to {state} at {device.last_updated}"
            print(msg)
            log_to_discord(msg)
    except Exception as e:
        error_msg = f"DB update failed for '{name}' to {state}: {e}"
        print(error_msg)
        log_to_discord(error_msg, is_error=True)

# Light controls with logging
def turn_on_light():
    try:
        os.system('mosquitto_pub -h localhost -t home/light1 -m "ON"')
        print("Light turned ON")
        update_device_status("parking light", "ON")
    except Exception as e:
        log_to_discord(f"Failed to turn ON light: {e}", is_error=True)

def turn_off_light():
    try:
        os.system('mosquitto_pub -h localhost -t home/light1 -m "OFF"')
        print("Light turned OFF")
        update_device_status("parking light", "OFF")
    except Exception as e:
        log_to_discord(f"Failed to turn OFF light: {e}", is_error=True)

# Refresh schedule from DB
def refresh_schedule():
    with app.app_context():
        schedule.clear()
        task_on = ScheduledTask.query.filter_by(device_name="parking light", action="turn_on").first()
        task_off = ScheduledTask.query.filter_by(device_name="parking light", action="turn_off").first()
        print("Time On:", task_on.time if task_on else "None", "Time OFF:", task_off.time if task_off else "None")

        if task_on and task_on.time:
            schedule.every().day.at(task_on.time).do(turn_on_light)
            print(f"Scheduled ON at {task_on.time}")

        if task_off and task_off.time:
            schedule.every().day.at(task_off.time).do(turn_off_light)
            print(f"Scheduled OFF at {task_off.time}")

# Initial load
refresh_schedule()

# Reload schedule every minute
schedule.every(1).minutes.do(refresh_schedule)

print("💡 MQTT Light Scheduler running...")

# Main loop
while True:
    schedule.run_pending()
    time.sleep(1)
