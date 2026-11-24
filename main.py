import uvicorn
from fastapi import FastAPI

from app.api.bookings import router
from app.core.config import settings

app = FastAPI(
    title="reservation_service",
    version="0.0.1",
    description="Booking creations service",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG,
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
