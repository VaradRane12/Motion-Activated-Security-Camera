import os
import time
import schedule
from datetime import datetime

# Setup Flask app context and SQLAlchemy
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/pi/test/Motion-Activated-Security-Camera/flask/instance/lights.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

def update_device_status(name, state):
    with app.app_context():
        device = Device.query.filter_by(name=name).first()
        if not device:
            device = Device(name=name, status=state, last_updated=datetime.utcnow())
            db.session.add(device)
        else:
            device.status = state
            device.last_updated = datetime.utcnow()
        db.session.commit()
        print(f"Device '{name}' updated to {state} at {device.last_updated}")

def turn_on_light():
    os.system('mosquitto_pub -h localhost -t home/light1 -m "ON"')
    print("Light turned ON")
    update_device_status("parking light", "ON")

def turn_off_light():
    os.system('mosquitto_pub -h localhost -t home/light1 -m "OFF"')
    print("Light turned OFF")
    update_device_status("parking light", "OFF")

def refresh_schedule():
    with app.app_context():
        schedule.clear()
        task_on = ScheduledTask.query.filter_by(device_name="parking light", action="turn_on").first()
        task_off = ScheduledTask.query.filter_by(device_name="parking light", action="turn_off").first()
        print("Time On: ",task_on.time, "Time OFF: ",task_off.time)
        if task_on and task_on.time:
            schedule.every().day.at(task_on.time).do(turn_on_light)
            print(f"Scheduled ON at {task_on.time}")

        if task_off and task_off.time:
            schedule.every().day.at(task_off.time).do(turn_off_light)
            print(f"Scheduled OFF at {task_off.time}")

# Initial load
refresh_schedule()

# Reload the schedule every 1 minute
schedule.every(1).minutes.do(refresh_schedule)

print("MQTT Light Scheduler running...")

while True:
    schedule.run_pending()
    time.sleep(1)
