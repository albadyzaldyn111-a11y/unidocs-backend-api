import io

from app.models.enums import UserRole
from app.models.user import User
from tests.conftest import make_pdf_bytes


def _create_user(db_session, university_id, email, role):
    from app.core.security import hash_password

    user = User(
        email=email,
        password_hash=hash_password("password123"),
        full_name="Test",
        role=role,
        university_id=university_id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _login(client, email):
    return client.post("/api/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]


def test_download_history_records_entry(client, seed_taxonomy, db_session):
    ctx = seed_taxonomy()
    _create_user(db_session, ctx["university"].id, "uploader@test.com", UserRole.VERIFIED_UPLOADER)
    _create_user(db_session, ctx["university"].id, "mod@test.com", UserRole.MODERATOR)
    _create_user(db_session, ctx["university"].id, "reader@test.com", UserRole.STUDENT)
    up_token = _login(client, "uploader@test.com")
    mod_token = _login(client, "mod@test.com")
    reader_token = _login(client, "reader@test.com")

    upload_resp = client.post(
        "/api/files/upload",
        headers={"Authorization": f"Bearer {up_token}"},
        data={"subject_id": ctx["subject"].id, "title": "Downloadable"},
        files={"file": ("d.pdf", io.BytesIO(make_pdf_bytes(b"dl-content")), "application/pdf")},
    )
    file_id = upload_resp.json()["id"]
    client.post(f"/api/moderation/files/{file_id}/approve", headers={"Authorization": f"Bearer {mod_token}"})

    client.get(
        f"/api/files/{file_id}/download",
        params={"university_id": ctx["university"].id},
        headers={"Authorization": f"Bearer {reader_token}"},
    )

    history = client.get("/api/users/me/downloads", headers={"Authorization": f"Bearer {reader_token}"})
    assert history.status_code == 200
    assert any(h["file_id"] == file_id for h in history.json())


def test_my_requests_endpoint_scoped_to_caller(client, seed_taxonomy, db_session):
    ctx = seed_taxonomy()
    _create_user(db_session, ctx["university"].id, "stu1@test.com", UserRole.STUDENT)
    _create_user(db_session, ctx["university"].id, "stu2@test.com", UserRole.STUDENT)
    token1 = _login(client, "stu1@test.com")
    token2 = _login(client, "stu2@test.com")

    client.post("/api/requests", json={"reason": "r1"}, headers={"Authorization": f"Bearer {token1}"})

    mine1 = client.get("/api/requests/mine", headers={"Authorization": f"Bearer {token1}"})
    mine2 = client.get("/api/requests/mine", headers={"Authorization": f"Bearer {token2}"})
    assert len(mine1.json()) == 1
    assert len(mine2.json()) == 0


def test_admin_can_create_university_without_code_change(client, seed_taxonomy, db_session):
    ctx = seed_taxonomy()
    _create_user(db_session, ctx["university"].id, "admin3@test.com", UserRole.ADMINISTRATOR)
    token = _login(client, "admin3@test.com")

    resp = client.post(
        "/api/admin/universities",
        json={"name": "جامعة جديدة", "name_en": "New University", "city": "City"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201

    listed = client.get("/api/taxonomy/universities")
    names = [u["name_en"] for u in listed.json()]
    assert "New University" in names
