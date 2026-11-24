from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.booking import BookingService


def get_booking_service(session: AsyncSession = Depends(get_db)) -> BookingService:
    return BookingService(session)
