def register_and_login(client, seed_taxonomy, email="student@test.com", password="password123"):
    ctx = seed_taxonomy()
    university_id = ctx["university"].id
    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Test User", "university_id": university_id},
    )
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return token, ctx


def test_register_and_login(client, seed_taxonomy):
    token, ctx = register_and_login(client, seed_taxonomy)
    assert token

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "student@test.com"
    assert me.json()["role"] == "student"


def test_login_wrong_password_rejected(client, seed_taxonomy):
    register_and_login(client, seed_taxonomy)
    resp = client.post("/api/auth/login", json={"email": "student@test.com", "password": "wrongpass"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_CREDENTIALS"


def test_protected_route_requires_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
    assert resp.json()["code"] == "UNAUTHENTICATED"


def test_student_cannot_access_moderation(client, seed_taxonomy):
    token, _ = register_and_login(client, seed_taxonomy)
    resp = client.get("/api/moderation/files", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert resp.json()["code"] == "FORBIDDEN"


def test_student_cannot_access_admin(client, seed_taxonomy):
    token, _ = register_and_login(client, seed_taxonomy)
    resp = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
