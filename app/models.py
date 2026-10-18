from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.timeutils import ISTDateTime, now_ist


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(ISTDateTime, default=now_ist)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")


class FitnessClass(Base):
    __tablename__ = "fitness_classes"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_capacity_positive"),
        CheckConstraint(
            "available_slots >= 0 AND available_slots <= capacity", name="ck_slots_range"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    instructor: Mapped[str] = mapped_column(String(100))
    start_time: Mapped[datetime] = mapped_column(ISTDateTime, index=True)
    capacity: Mapped[int] = mapped_column(Integer)
    available_slots: Mapped[int] = mapped_column(Integer)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(ISTDateTime, default=now_ist)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="fitness_class")


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("class_id", "client_email", name="uq_class_client"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("fitness_classes.id"), index=True)
    client_name: Mapped[str] = mapped_column(String(100))
    client_email: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(ISTDateTime, default=now_ist)

    user: Mapped[User] = relationship(back_populates="bookings")
    fitness_class: Mapped[FitnessClass] = relationship(back_populates="bookings")