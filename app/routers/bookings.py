from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user
from app.models import Booking, FitnessClass, User
from app.schemas import BookingOut, BookRequest
from app.timeutils import now_ist, to_ist

router = APIRouter(tags=["bookings"])


def booking_out(b: Booking, fc: FitnessClass) -> BookingOut:
    return BookingOut(
        id=b.id,
        class_id=fc.id,
        class_name=fc.name,
        instructor=fc.instructor,
        date_time=to_ist(fc.start_time),
        client_name=b.client_name,
        client_email=b.client_email,
        booked_at=to_ist(b.created_at),
    )


@router.post("/book", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def book_class(
    body: BookRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fc = db.get(FitnessClass, body.class_id)
    if fc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")
    if fc.start_time <= now_ist():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Class has already started")

    booking = Booking(
        user_id=user.id,
        class_id=fc.id,
        client_name=body.client_name,
        client_email=str(body.client_email).lower(),
    )
    db.add(booking)
    try:
        db.flush()  # the unique (class_id, client_email) constraint fires here
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "This client is already booked in this class")

    # Atomic conditional decrement: succeeds only while a slot remains.
    result = db.execute(
        update(FitnessClass)
        .where(FitnessClass.id == fc.id, FitnessClass.available_slots > 0)
        .values(available_slots=FitnessClass.available_slots - 1)
    )
    if result.rowcount != 1:
        db.rollback()  # also discards the pending booking row
        raise HTTPException(status.HTTP_409_CONFLICT, "Class is fully booked")

    db.commit()
    db.refresh(booking)
    return booking_out(booking, fc)


@router.get("/bookings", response_model=list[BookingOut])
def my_bookings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.scalars(
        select(Booking)
        .where(Booking.user_id == user.id)
        .options(joinedload(Booking.fitness_class))
        .order_by(Booking.created_at.desc(), Booking.id.desc())
    ).all()
    return [booking_out(b, b.fitness_class) for b in rows]