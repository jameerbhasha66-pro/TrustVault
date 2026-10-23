
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
import models  # Ensure all models are registered


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def register_user(client, username):
    response = client.post(
        "/register",
        json={
            "username": username,
            "password": "TrustVault-Test-2026!",
        },
    )
    assert response.status_code == 201, response.text


def login_user(client, username):
    response = client.post(
        "/login",
        json={
            "username": username,
            "password": "TrustVault-Test-2026!",
        },
    )
    assert response.status_code == 200, response.text


def test_share_list_download_and_revoke(client):
    register_user(client, "owner_test")
    register_user(client, "recipient_test")

    # Owner logs in and uploads a harmless test file.
    login_user(client, "owner_test")
    upload = client.post(
        "/documents/",
        files={
            "file": (
                "sharing_test.txt",
                b"TrustVault automated sharing test",
                "text/plain",
            )
        },
        data={"category": "Testing"},
    )
    assert upload.status_code in (200, 201), upload.text
    document_id = upload.json()["id"]

    # Owner grants read-only access.
    share = client.post(
        f"/documents/{document_id}/share",
        json={
            "username": "recipient_test",
            "can_read": True,
            "can_edit": False,
        },
    )
    assert share.status_code == 200, share.text

    # Recipient cannot grant access to someone else.
    client.post("/logout")
    login_user(client, "recipient_test")

    forbidden_share = client.post(
        f"/documents/{document_id}/share",
        json={
            "username": "owner_test",
            "can_read": True,
            "can_edit": False,
        },
    )
    assert forbidden_share.status_code == 403

    # Recipient can see and download the shared document.
    listing = client.get("/documents/")
    assert listing.status_code == 200
    assert any(item["id"] == document_id for item in listing.json())

    download = client.get(f"/documents/{document_id}/download")
    assert download.status_code == 200
    assert download.content == b"TrustVault automated sharing test"

    # Owner revokes access.
    client.post("/logout")
    login_user(client, "owner_test")

    revoke = client.delete(
        f"/documents/{document_id}/share/recipient_test"
    )
    assert revoke.status_code == 200, revoke.text

    # Recipient can no longer see or download the document.
    client.post("/logout")
    login_user(client, "recipient_test")

    listing_after_revoke = client.get("/documents/")
    assert listing_after_revoke.status_code == 200
    assert all(
        item["id"] != document_id
        for item in listing_after_revoke.json()
    )

    denied_download = client.get(
        f"/documents/{document_id}/download"
    )
    assert denied_download.status_code == 403
