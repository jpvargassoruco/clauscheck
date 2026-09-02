import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://postgres:test@localhost:5434/clauscheck"
)
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-bytes-long-for-hs256")
os.environ.setdefault("REDIS_URL", "redis://localhost:6399/0")
os.environ.setdefault("FERNET_KEY", "")
os.environ.setdefault("ADMIN_EMAIL", "admin@clauscheck.local")
os.environ.setdefault("ADMIN_PASSWORD", "changeme-test")

import pytest
import pytest_asyncio
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from alembic import command
from app.db import engine
from app.main import app
from app.models import Plan
from app.queue import get_arq_pool

_ALEMBIC_INI = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")

_TABLES = [
    "analyses",
    "usage",
    "invitations",
    "memberships",
    "documents",
    "articulos",
    "cuerpos_legales",
    "orgs",
    "llm_providers",
    "users",
    "plans",
]


class FakeArqPool:
    def __init__(self):
        self.enqueued: list[tuple] = []

    async def enqueue_job(self, name, *args, **kwargs):
        self.enqueued.append((name, args, kwargs))
        return None

    async def ping(self):
        return True


@pytest.fixture(scope="session", autouse=True)
def _migrate_db():
    cfg = Config(_ALEMBIC_INI)
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(_ALEMBIC_INI), "alembic"))
    command.upgrade(cfg, "head")
    yield


@pytest_asyncio.fixture(autouse=True)
async def _clean_db():
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY CASCADE"))
    yield


@pytest_asyncio.fixture(autouse=True)
async def _seed_plans():
    from app.db import async_session_maker

    async with async_session_maker() as db:
        db.add(Plan(code="free", nombre="Free", analisis_mes=5, docs_max=10, precio_bob=0))
        db.add(Plan(code="pro", nombre="Pro", analisis_mes=50, docs_max=200, precio_bob=150))
        db.add(
            Plan(code="despacho", nombre="Despacho", analisis_mes=500, docs_max=2000, precio_bob=800)
        )
        await db.commit()


@pytest.fixture(autouse=True)
def _stub_paperless(monkeypatch):
    from app import paperless

    async def _fake_provision_org(slug, org_id):
        return paperless.PaperlessOrgResources(user_id=1, tag_id=1, storage_path_id=1)

    async def _fake_upload_document(*args, **kwargs):
        return 1

    async def _fake_set_owner_permissions(*args, **kwargs):
        return None

    monkeypatch.setattr(paperless, "provision_org", _fake_provision_org)
    monkeypatch.setattr(paperless, "upload_document", _fake_upload_document)
    monkeypatch.setattr(paperless, "set_owner_permissions", _fake_set_owner_permissions)
    monkeypatch.setattr("app.routers.orgs.provision_org", _fake_provision_org)
    monkeypatch.setattr("app.routers.auth.provision_org", _fake_provision_org)
    monkeypatch.setattr("app.routers.documents.upload_document", _fake_upload_document)
    monkeypatch.setattr("app.routers.documents.set_owner_permissions", _fake_set_owner_permissions)


@pytest.fixture
def fake_arq_pool():
    return FakeArqPool()


@pytest_asyncio.fixture
async def client(fake_arq_pool):
    async def _get_fake_pool():
        return fake_arq_pool

    app.dependency_overrides[get_arq_pool] = _get_fake_pool
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
