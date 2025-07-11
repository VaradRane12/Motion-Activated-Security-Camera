from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(10), default='OFF')  
class ScheduledTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(100), default = " ")
    time = db.Column(db.String(5))  
    action = db.Column(db.String(20))  