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
    resp = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    return resp.json()["access_token"]


def test_upload_requires_uploader_role(client, seed_taxonomy, db_session):
    ctx = seed_taxonomy()
    _create_user(db_session, ctx["university"].id, "student@test.com", UserRole.STUDENT)
    token = _login(client, "student@test.com")

    resp = client.post(
        "/api/files/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"subject_id": ctx["subject"].id, "title": "Lecture 1"},
        files={"file": ("lecture.pdf", io.BytesIO(make_pdf_bytes()), "application/pdf")},
    )
    assert resp.status_code == 403


def test_upload_success_and_duplicate_rejected(client, seed_taxonomy, db_session):
    ctx = seed_taxonomy()
    _create_user(db_session, ctx["university"].id, "uploader@test.com", UserRole.VERIFIED_UPLOADER)
    token = _login(client, "uploader@test.com")
    pdf = make_pdf_bytes(b"unique-content-1")

    resp = client.post(
        "/api/files/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"subject_id": ctx["subject"].id, "title": "Lecture 1"},
        files={"file": ("lecture.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"

    dup_resp = client.post(
        "/api/files/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"subject_id": ctx["subject"].id, "title": "Lecture 1 copy"},
        files={"file": ("lecture_copy.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert dup_resp.status_code == 409
    assert dup_resp.json()["code"] == "DUPLICATE_FILE"


def test_non_pdf_rejected(client, seed_taxonomy, db_session):
    ctx = seed_taxonomy()
    _create_user(db_session, ctx["university"].id, "uploader2@test.com", UserRole.VERIFIED_UPLOADER)
    token = _login(client, "uploader2@test.com")

    resp = client.post(
        "/api/files/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"subject_id": ctx["subject"].id, "title": "Not a PDF"},
        files={"file": ("notes.pdf", io.BytesIO(b"NOT_A_PDF_HEADER"), "application/pdf")},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "INVALID_FILE_TYPE"


def test_moderation_approve_flow_and_reject_requires_reason(client, seed_taxonomy, db_session):
    ctx = seed_taxonomy()
    _create_user(db_session, ctx["university"].id, "uploader3@test.com", UserRole.VERIFIED_UPLOADER)
    _create_user(db_session, ctx["university"].id, "mod@test.com", UserRole.MODERATOR)
    up_token = _login(client, "uploader3@test.com")
    mod_token = _login(client, "mod@test.com")

    upload_resp = client.post(
        "/api/files/upload",
        headers={"Authorization": f"Bearer {up_token}"},
        data={"subject_id": ctx["subject"].id, "title": "Lecture X"},
        files={"file": ("x.pdf", io.BytesIO(make_pdf_bytes(b"content-x")), "application/pdf")},
    )
    file_id = upload_resp.json()["id"]

    lock_resp = client.post(f"/api/moderation/files/{file_id}/lock", headers={"Authorization": f"Bearer {mod_token}"})
    assert lock_resp.status_code == 200

    reject_no_reason = client.post(
        f"/api/moderation/files/{file_id}/reject", json={"reason": ""}, headers={"Authorization": f"Bearer {mod_token}"}
    )
    assert reject_no_reason.status_code == 422

    approve_resp = client.post(
        f"/api/moderation/files/{file_id}/approve", headers={"Authorization": f"Bearer {mod_token}"}
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"


def test_moderation_lock_blocks_other_moderator(client, seed_taxonomy, db_session):
    ctx = seed_taxonomy()
    _create_user(db_session, ctx["university"].id, "uploader4@test.com", UserRole.VERIFIED_UPLOADER)
    _create_user(db_session, ctx["university"].id, "mod1@test.com", UserRole.MODERATOR)
    _create_user(db_session, ctx["university"].id, "mod2@test.com", UserRole.MODERATOR)
    up_token = _login(client, "uploader4@test.com")
    mod1_token = _login(client, "mod1@test.com")
    mod2_token = _login(client, "mod2@test.com")

    upload_resp = client.post(
        "/api/files/upload",
        headers={"Authorization": f"Bearer {up_token}"},
        data={"subject_id": ctx["subject"].id, "title": "Lecture Y"},
        files={"file": ("y.pdf", io.BytesIO(make_pdf_bytes(b"content-y")), "application/pdf")},
    )
    file_id = upload_resp.json()["id"]

    client.post(f"/api/moderation/files/{file_id}/lock", headers={"Authorization": f"Bearer {mod1_token}"})
    second_lock = client.post(f"/api/moderation/files/{file_id}/lock", headers={"Authorization": f"Bearer {mod2_token}"})
    assert second_lock.status_code == 409
    assert second_lock.json()["code"] == "FILE_LOCKED"
