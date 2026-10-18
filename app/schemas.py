from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.timeutils import to_ist


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v

    @field_validator("password")
    @classmethod
    def bcrypt_byte_limit(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("password must be at most 72 bytes")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def as_ist(cls, v: datetime) -> datetime:
        return to_ist(v)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ClassCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=100)
    date_time: datetime = Field(alias="dateTime")
    instructor: str = Field(min_length=1, max_length=100)
    available_slots: int = Field(alias="availableSlots", ge=1, le=1000)

    @field_validator("name", "instructor")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class ClassOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    date_time: datetime = Field(serialization_alias="dateTime")
    instructor: str
    available_slots: int = Field(serialization_alias="availableSlots")


class BookRequest(BaseModel):
    class_id: int
    client_name: str = Field(min_length=1, max_length=100)
    client_email: EmailStr

    @field_validator("client_name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("client_name must not be blank")
        return v


class BookingOut(BaseModel):
    id: int
    class_id: int
    class_name: str
    instructor: str
    date_time: datetime = Field(serialization_alias="dateTime")
    client_name: str
    client_email: EmailStr
    booked_at: datetime