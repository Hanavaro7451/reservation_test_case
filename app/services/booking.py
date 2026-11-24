from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.repositories.booking import BookingRepository, is_active_slot_conflict
from app.schemas.booking import BookingCreate
from app.services.exceptions import BookingNotFoundError, SlotAlreadyBookedError


class BookingService:

    def __init__(self, session: AsyncSession):
        self.repo = BookingRepository(session)
        self.session = session

    async def create(self, booking: BookingCreate) -> Booking:
        booking = Booking(
            **booking.model_dump(),
            status=BookingStatus.ACTIVE
        )

        if await self.repo.get_active_slot(booking.booking_date, booking.booking_time) is not None:
            raise SlotAlreadyBookedError("Slot is already booked")
        try:
            await self.repo.create(booking)
            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            if is_active_slot_conflict(error):
                raise SlotAlreadyBookedError("Slot is already booked") from error
            raise

        return booking

    async def get_all(self, booking_date: date | None = None) -> list[Booking]:
        return await self.repo.get_all(booking_date)

    async def get_by_id(self, booking_id: int) -> Booking:
        booking = await self.repo.get_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundError("Booking not found")
        return booking

    async def cancel(self, booking_id: int) -> Booking:
        booking = await self.get_by_id(booking_id)
        booking.status = BookingStatus.CANCELED
        await self.session.commit()
        return booking
