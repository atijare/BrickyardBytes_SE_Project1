from conftest import register_and_login


def test_register_login_and_me_flow(app_client):
    payload = {"email": "test@ncsu.edu", "password": "secret"}

    # Register
    r = app_client.post("/auth/register", json=payload)
    assert r.status_code in (200, 201), r.text
    data = r.json()
    assert "token" in data and "user" in data
    assert data["user"]["username"] == payload["email"]


    # Duplicate register -> 409
    r_dup = app_client.post("/auth/register", json=payload)
    assert r_dup.status_code == 409

    # Login
    r2 = app_client.post("/auth/login", json=payload)
    assert r2.status_code == 200, r2.text
    token = r2.json()["token"]

    # Me
    headers = {"Authorization": f"Bearer {token}"}
    r3 = app_client.get("/auth/me", headers=headers)
    assert r3.status_code == 200, r3.text
    assert r3.json()["username"] == payload["email"]
