from datetime import time, date
from sqlite3 import IntegrityError as SQLiteIntegrityError
from sqlite3 import SQLITE_CONSTRAINT_UNIQUE

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.enums import BookingStatus


def is_active_slot_conflict(error: IntegrityError) -> bool:
    cause = error.orig
    return (
        isinstance(cause, SQLiteIntegrityError)
        and getattr(cause, "sqlite_errorcode", None) == SQLITE_CONSTRAINT_UNIQUE
        and str(cause) == "UNIQUE constraint failed: booking.booking_date, booking.booking_time"
    )


class BookingRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, booking: Booking) -> Booking:
        self.session.add(booking)
        await self.session.flush()
        await self.session.refresh(booking)
        return booking

    async def get_active_slot(self, booking_date: date, booking_time: time) -> Booking | None:
        query = select(Booking).filter(
            Booking.booking_date == booking_date,
            Booking.booking_time == booking_time,
            Booking.status == BookingStatus.ACTIVE
        )
        booking = await self.session.scalar(query)
        return booking if booking else None

    async def get_all(self, booking_date: date | None = None) -> list[Booking]:
        query = select(Booking).order_by(Booking.id)
        if booking_date is not None:
            query = query.where(Booking.booking_date == booking_date)

        bookings = await self.session.scalars(query)
        return list(bookings.all())

    async def get_by_id(self, booking_id: int) -> Booking | None:
        return await self.session.get(Booking, booking_id)
