from app import app, db
from models import Light

with app.app_context():
    light1 = Light(name="parking light", room="parking")
    db.session.add(light1)
    db.session.commit()
