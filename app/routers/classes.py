from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import FitnessClass, User
from app.schemas import ClassCreate, ClassOut
from app.timeutils import IST, now_ist, to_ist, to_tz

router = APIRouter(tags=["classes"])


def class_out(fc: FitnessClass, tz: ZoneInfo = IST) -> ClassOut:
    return ClassOut(
        id=fc.id,
        name=fc.name,
        date_time=to_tz(fc.start_time, tz),
        instructor=fc.instructor,
        available_slots=fc.available_slots,
    )


@router.post("/classes", response_model=ClassOut, status_code=status.HTTP_201_CREATED)
def create_class(
    body: ClassCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fc = FitnessClass(
        name=body.name,
        instructor=body.instructor,
        start_time=to_ist(body.date_time),
        capacity=body.available_slots,
        available_slots=body.available_slots,
        created_by=user.id,
    )
    db.add(fc)
    db.commit()
    db.refresh(fc)
    return class_out(fc)


@router.get("/classes", response_model=list[ClassOut])
def list_upcoming_classes(
    tz: str | None = Query(
        default=None,
        description="IANA timezone for output, e.g. UTC or America/New_York. Default: IST.",
    ),
    db: Session = Depends(get_db),
):
    zone = IST
    if tz:
        try:
            zone = ZoneInfo(tz)
        except (ZoneInfoNotFoundError, ValueError, OSError):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown timezone: {tz}")
    rows = db.scalars(
        select(FitnessClass)
        .where(FitnessClass.start_time > now_ist())
        .order_by(FitnessClass.start_time, FitnessClass.id)
    ).all()
    return [class_out(fc, zone) for fc in rows]