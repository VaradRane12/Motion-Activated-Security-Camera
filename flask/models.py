from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    status = db.Column(db.String(10))
    room = db.Column(db.String(50))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
