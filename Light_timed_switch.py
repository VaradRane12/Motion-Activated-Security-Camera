import os
import time
import schedule
from datetime import datetime

# Setup Flask app context and SQLAlchemy
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask/instance/lights.db'  # relative to your project root
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(10), default='OFF')

def update_device_status(name, state):
    with app.app_context():
        device = Device.query.filter_by(name=name).first()
        if not device:
            # Create device if it doesn't exist
            device = Device(name=name, status=state, last_updated=datetime.utcnow())
            db.session.add(device)
        else:
            device.status = state
            device.last_updated = datetime.utcnow()
        db.session.commit()
        print(f"Device '{name}' updated to {state} at {device.last_updated}")

def turn_on_light():
    os.system('mosquitto_pub -h localhost -t home/light1 -m "ON"')
    print("Light turned ON at 18:30")
    update_device_status("light1", "ON")

def turn_off_light():
    os.system('mosquitto_pub -h localhost -t home/light1 -m "OFF"')
    print("Light turned OFF at 05:30")
    update_device_status("light1", "OFF")

# Scheduler
schedule.every().day.at("18:30").do(turn_on_light)
schedule.every().day.at("05:30").do(turn_off_light)

print("MQTT Light Scheduler running...")

while True:
    schedule.run_pending()
    time.sleep(1)
