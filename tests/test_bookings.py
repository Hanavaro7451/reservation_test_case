import asyncio
from datetime import date, datetime, time, timedelta

import pytest
from httpx import AsyncClient

from app.models.booking import Booking
from app.repositories.booking import BookingRepository
from app.schemas.booking import organization_timezone


pytestmark = pytest.mark.anyio


@pytest.fixture
def booking_payload() -> dict[str, str | int]:
    tomorrow = datetime.now(organization_timezone).date() + timedelta(days=1)
    return {
        "name": "Test guest",
        "phone": "+79999999999",
        "booking_date": tomorrow.isoformat(),
        "booking_time": "17:00",
        "guests": 2,
    }


async def test_parallel_bookings_conflict(
    client: AsyncClient,
    booking_payload: dict[str, str | int],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid = await client.post("/bookings", json={**booking_payload, "booking_time": "17:30"})
    assert invalid.status_code == 422
    assert invalid.json()["detail"][0]["loc"] == ["body", "booking_time"]

    both_checked_slot = asyncio.Barrier(2)
    get_active_slot = BookingRepository.get_active_slot

    async def observe_free_slot(
        repo: BookingRepository, booking_date: date, booking_time: time,
    ) -> Booking | None:
        booking = await get_active_slot(repo, booking_date, booking_time)
        assert booking is None
        # Let both requests finish the lookup before either can attempt an insert.
        await both_checked_slot.wait()
        return booking

    with monkeypatch.context() as patch:
        patch.setattr(BookingRepository, "get_active_slot", observe_free_slot)
        async with asyncio.timeout(10):
            replies = await asyncio.gather(
                client.post("/bookings", json=booking_payload),
                client.post("/bookings", json=booking_payload),
            )

    created, conflict = sorted(replies, key=lambda reply: reply.status_code)
    assert created.status_code == 201
    assert created.json()["status"] == "active"
    assert conflict.status_code == 409
    assert conflict.json() == {"detail": "Slot is already booked"}

    bookings = await client.get("/bookings")
    assert bookings.status_code == 200
    assert bookings.json() == [created.json()]


async def test_cancelled_booking_releases_slot(
    client: AsyncClient, booking_payload: dict[str, str | int],
) -> None:
    created = await client.post("/bookings", json=booking_payload)
    assert created.status_code == 201
    original = created.json()
    path = f"/bookings/{original['id']}"

    cancelled = await client.delete(path)
    assert cancelled.status_code == 200
    assert cancelled.json() == {**original, "status": "cancelled"}

    rebooked = await client.post("/bookings", json=booking_payload)
    assert rebooked.status_code == 201
    assert rebooked.json()["id"] != original["id"]
    assert rebooked.json()["status"] == "active"

    retained = await client.get(path)
    assert retained.status_code == 200
    assert retained.json() == cancelled.json()


async def test_read_bookings_with_date_filter(
    client: AsyncClient, booking_payload: dict[str, str | int],
) -> None:
    first_date = str(booking_payload["booking_date"])
    second_date = date.fromisoformat(first_date) + timedelta(days=1)

    first = await client.post("/bookings", json=booking_payload)
    second = await client.post("/bookings", json={**booking_payload, "booking_date": second_date.isoformat()})
    assert first.status_code == second.status_code == 201

    all_bookings = await client.get("/bookings")
    assert all_bookings.status_code == 200
    assert all_bookings.json() == [first.json(), second.json()]

    filtered = await client.get("/bookings", params={"date": first_date})
    assert filtered.status_code == 200
    assert filtered.json() == [first.json()]

    missing = await client.get(f"/bookings/{second.json()['id'] + 1}")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Booking not found"}
