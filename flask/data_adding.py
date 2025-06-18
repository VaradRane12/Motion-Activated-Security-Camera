from app import app, db
from models import Device

with app.app_context():
    light1 = Device(name="parking light", room="parking")
    db.session.add(light1)
    db.session.commit()
