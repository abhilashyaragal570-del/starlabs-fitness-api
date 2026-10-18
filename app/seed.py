from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import FitnessClass, User
from app.security import hash_password
from app.timeutils import IST, now_ist

DEMO_NAME = "Demo Admin"
DEMO_EMAIL = "demo@starlabs.example"
DEMO_PASSWORD = "DemoPass123"

# (name, instructor, days from today, hour IST, minute, slots)
CLASSES = [
    ("Yoga Flow", "Priya Sharma", 1, 7, 0, 20),
    ("HIIT Session", "Rahul Verma", 1, 18, 30, 10),
    ("Zumba Party", "Anita Desai", 2, 19, 0, 15),
    ("Strength Training", "Karan Mehta", 3, 6, 30, 8),
    ("Pilates Core", "Sneha Iyer", 4, 8, 0, 12),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(name=DEMO_NAME, email=DEMO_EMAIL, hashed_password=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.commit()
            print(f"Created demo user {DEMO_EMAIL} / {DEMO_PASSWORD}")
        else:
            print("Demo user already exists")

        if db.scalar(select(FitnessClass.id).limit(1)) is not None:
            print("Classes already exist; skipping class seed")
            return

        today = now_ist().date()
        for name, instructor, days, hour, minute, slots in CLASSES:
            start = datetime(today.year, today.month, today.day, hour, minute, tzinfo=IST) + timedelta(days=days)
            db.add(
                FitnessClass(
                    name=name,
                    instructor=instructor,
                    start_time=start,
                    capacity=slots,
                    available_slots=slots,
                    created_by=user.id,
                )
            )
        db.commit()
        print(f"Seeded {len(CLASSES)} classes")


if __name__ == "__main__":
    seed()