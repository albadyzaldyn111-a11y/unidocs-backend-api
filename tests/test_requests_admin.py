from app.models.enums import UserRole
from app.models.user import User


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


def test_upload_request_promotes_student_to_uploader(client, seed_taxonomy, db_session):
    ctx = seed_taxonomy()
    _create_user(db_session, ctx["university"].id, "stu@test.com", UserRole.STUDENT)
    _create_user(db_session, ctx["university"].id, "mod@test.com", UserRole.MODERATOR)
    stu_token = _login(client, "stu@test.com")
    mod_token = _login(client, "mod@test.com")

    create_resp = client.post(
        "/api/requests", json={"reason": "I want to share my notes"}, headers={"Authorization": f"Bearer {stu_token}"}
    )
    assert create_resp.status_code == 201
    request_id = create_resp.json()["id"]

    # Duplicate pending request blocked
    dup = client.post("/api/requests", json={"reason": "again"}, headers={"Authorization": f"Bearer {stu_token}"})
    assert dup.status_code == 409

    approve = client.post(
        f"/api/requests/{request_id}/approve", json={"note": "welcome"}, headers={"Authorization": f"Bearer {mod_token}"}
    )
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {stu_token}"})
    assert me.json()["role"] == "verified_uploader"

    notifications = client.get("/api/notifications", headers={"Authorization": f"Bearer {stu_token}"})
    assert any(n["type"] == "upload_request_approved" for n in notifications.json())


def test_admin_stats_and_non_admin_forbidden(client, seed_taxonomy, db_session):
    ctx = seed_taxonomy()
    _create_user(db_session, ctx["university"].id, "admin@test.com", UserRole.ADMINISTRATOR)
    _create_user(db_session, ctx["university"].id, "mod@test.com", UserRole.MODERATOR)
    admin_token = _login(client, "admin@test.com")
    mod_token = _login(client, "mod@test.com")

    stats = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert stats.status_code == 200
    assert "total_users" in stats.json()

    forbidden = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {mod_token}"})
    assert forbidden.status_code == 403


def test_admin_can_update_settings(client, seed_taxonomy, db_session):
    ctx = seed_taxonomy()
    _create_user(db_session, ctx["university"].id, "admin2@test.com", UserRole.ADMINISTRATOR)
    token = _login(client, "admin2@test.com")

    resp = client.put(
        "/api/admin/settings/max_file_size_mb", json={"value": "80"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200

    settings = client.get("/api/admin/settings", headers={"Authorization": f"Bearer {token}"})
    assert settings.json()["max_file_size_mb"] == "80"
