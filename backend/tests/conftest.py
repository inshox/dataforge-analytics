import asyncio
import os
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Isolated data dir per test session
_test_root = tempfile.mkdtemp(prefix="dataforge_test_")
os.environ["DATAFORGE_DATA_DIR"] = _test_root
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_test_root}/test.db"
os.environ["SEED_DEMO_ON_STARTUP"] = "false"
os.environ["PORT"] = "8765"

from app.core.config import get_settings  # noqa: E402
from app.core.database import init_db  # noqa: E402
from app.main import app  # noqa: E402

get_settings.cache_clear()
asyncio.run(init_db())


@pytest.fixture
def sample_csv() -> bytes:
    path = Path(__file__).resolve().parent.parent / "app" / "data" / "demo_sales.csv"
    return path.read_bytes()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
