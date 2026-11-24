from datetime import date, time

from sqlalchemy import Date, Enum, Index, Integer, String, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models.enums import BookingStatus


class Base(DeclarativeBase):
    pass


class Booking(Base):
    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(12), nullable=False)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    booking_time: Mapped[time] = mapped_column(Time, nullable=False)
    guests: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.ACTIVE)

    __table_args__ = (
        Index(
            "uq_booking_active_slot",
            "booking_date",
            "booking_time",
            unique=True,
            sqlite_where=status == BookingStatus.ACTIVE,
        ),
    )
