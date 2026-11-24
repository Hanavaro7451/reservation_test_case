import re
from datetime import date, time, datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.models.enums import BookingStatus

organization_timezone = ZoneInfo("Europe/Moscow")

class BookingCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    phone: str = Field(pattern=r"^\+7[0-9]{10}$")
    booking_date: date
    booking_time: time
    guests: int = Field(ge=1, le=10)

    @field_validator("booking_date", mode='before')
    @classmethod
    def validate_date_format(cls, field: object) -> str:
        if not isinstance(field, str) or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}", field
        ):
            raise ValueError('Use format YYYY-MM-DD for date')
        return field

    @field_validator("booking_time", mode='before')
    @classmethod
    def validate_time_format(cls, field: object) -> str:
        if not isinstance(field, str) or not re.fullmatch(
            r"(?:1[2-9]|2[0-2]):00", field
        ):
            raise ValueError("Choose a whole hour from 12:00 to 22:00")
        return field

    @model_validator(mode="after")
    def validate_booking_slot(self) -> "BookingCreate":
        now = datetime.now(organization_timezone)
        days_ahead = (self.booking_date - now.date()).days
        if not 0 <= days_ahead <= 30:
            raise ValueError("Choose a date from today through 30 days ahead")

        if days_ahead == 0 and self.booking_time < now.time():
            raise ValueError("This time slot has already passed")

        return self


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    booking_date: date
    booking_time: time
    guests: int
    status: BookingStatus
