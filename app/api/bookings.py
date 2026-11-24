from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_booking_service
from app.schemas.booking import BookingCreate, BookingOut
from app.services.booking import BookingService
from app.services.exceptions import BookingNotFoundError, SlotAlreadyBookedError

router = APIRouter()


@router.post("/bookings", response_model=BookingOut, status_code=201)
async def create_booking(
    payload: BookingCreate,
    service: BookingService = Depends(get_booking_service),
) -> BookingOut:
    try:
        booking = await service.create(payload)
    except SlotAlreadyBookedError as err:
        raise HTTPException(status_code=409, detail=str(err)) from err
    return BookingOut.model_validate(booking)


@router.get("/bookings", response_model=list[BookingOut], status_code=200)
async def get_bookings(
    booking_date: date | None = Query(default=None, alias="date"),
    service: BookingService = Depends(get_booking_service),
) -> list[BookingOut]:
    bookings = await service.get_all(booking_date)
    return [BookingOut.model_validate(booking) for booking in bookings]


@router.get("/bookings/{id}", response_model=BookingOut, status_code=200)
async def get_booking_by_id(
    id: int,
    service: BookingService = Depends(get_booking_service),
) -> BookingOut:
    try:
        booking = await service.get_by_id(id)
    except BookingNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    return BookingOut.model_validate(booking)


@router.delete("/bookings/{id}", response_model=BookingOut, status_code=200)
async def delete_booking_by_id(
    id: int,
    service: BookingService = Depends(get_booking_service),
) -> BookingOut:
    try:
        booking = await service.cancel(id)
    except BookingNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    return BookingOut.model_validate(booking)
