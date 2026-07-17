import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.worker import send_onboarding_email
from app.database import SessionLocal
from app.models import User

db = SessionLocal()
user = db.query(User).filter(User.personal_email == 'nikhilpatnaikmn360@gmail.com').first()
if user:
    print('User found:', user.name, user.id)
    task = send_onboarding_email.delay(user.id, 'Day 0', {'password': 'TestPass@123'})
    print('Task queued:', task.id)
else:
    print('User not found - check personal_email in database')