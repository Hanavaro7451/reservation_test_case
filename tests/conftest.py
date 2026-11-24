from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    database_path = (tmp_path / "bookings.db").as_posix()
    sync_url = f"sqlite:///{database_path}"
    async_url = f"sqlite+aiosqlite:///{database_path}"
    monkeypatch.setenv("DATABASE_SYNC_URL", sync_url)
    monkeypatch.setenv("DATABASE_URL", async_url)
    monkeypatch.setenv("DEBUG", "false")

    from app.core.config import settings
    from app.db.session import get_db
    from main import app

    monkeypatch.setattr(settings, "DATABASE_SYNC_URL", sync_url)
    config_path = Path(__file__).resolve().parents[1] / "alembic.ini"
    command.upgrade(Config(str(config_path)), "head")

    engine = create_async_engine(async_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def get_test_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    monkeypatch.setitem(app.dependency_overrides, get_db, get_test_db)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
    finally:
        await engine.dispose()
