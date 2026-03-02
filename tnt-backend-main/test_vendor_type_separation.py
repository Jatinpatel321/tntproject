from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.deps import get_db
from app.core.security import get_current_user
from app.database.base import Base
from app.main import app
from app.modules.users.model import User, UserRole


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@pytest.fixture()
def test_db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def seed_data(test_db_session):
    food_vendor = User(
        phone="8700000001",
        name="Food Vendor",
        role=UserRole.VENDOR,
        vendor_type="food",
        is_active=True,
        is_approved=True,
    )
    stationery_vendor = User(
        phone="8700000002",
        name="Stationery Vendor",
        role=UserRole.VENDOR,
        vendor_type="stationery",
        is_active=True,
        is_approved=True,
    )

    test_db_session.add_all([food_vendor, stationery_vendor])
    test_db_session.commit()
    test_db_session.refresh(food_vendor)
    test_db_session.refresh(stationery_vendor)

    return {"food_vendor": food_vendor, "stationery_vendor": stationery_vendor}


@pytest.fixture()
def auth_context(seed_data):
    vendor = seed_data["food_vendor"]
    return {"id": vendor.id, "phone": vendor.phone, "role": vendor.role.value}


@pytest.fixture()
def client(test_db_session, auth_context):
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    def override_get_current_user():
        return auth_context

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_vendor_type_separation_enforced(client, seed_data, auth_context, monkeypatch):
    monkeypatch.setattr("app.modules.menu.router.save_menu_image", lambda _image: "https://example.com/fake.png")

    food_vendor = seed_data["food_vendor"]
    stationery_vendor = seed_data["stationery_vendor"]

    auth_context.update({"id": food_vendor.id, "phone": food_vendor.phone, "role": food_vendor.role.value})
    food_menu_allowed = client.post(
        "/menu/",
        data={"name": "Dosa", "price": "50", "description": "Test"},
        files={"image": ("test.png", b"fake-image-bytes", "image/png")},
    )
    assert food_menu_allowed.status_code == 200

    food_stationery_denied = client.post(
        "/stationery/services",
        data={"name": "Print", "price_per_unit": "5", "unit": "page"},
    )
    assert food_stationery_denied.status_code == 403

    auth_context.update({"id": stationery_vendor.id, "phone": stationery_vendor.phone, "role": stationery_vendor.role.value})
    stationery_service_allowed = client.post(
        "/stationery/services",
        data={"name": "Print", "price_per_unit": "5", "unit": "page"},
    )
    assert stationery_service_allowed.status_code == 200

    stationery_menu_denied = client.post(
        "/menu/",
        data={"name": "Dosa", "price": "50", "description": "Test"},
        files={"image": ("test.png", b"fake-image-bytes", "image/png")},
    )
    assert stationery_menu_denied.status_code == 403
