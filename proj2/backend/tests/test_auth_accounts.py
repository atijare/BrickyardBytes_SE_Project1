from conftest import register_and_login


def test_register_rejects_non_ncsu(app_client):
    r = app_client.post(
        "/auth/register", json={"email": "user@gmail.com", "password": "x"}
    )
    assert r.status_code == 400, r.text
    assert "NCSU" in r.text or "ncsu" in r.text


def test_register_rejects_adversarial_input(app_client):
    r = app_client.post(
        "/auth/register", json={"email": "user@gmail.com", "password": "x"}
    )
    assert r.status_code == 400, r.text
    assert len(r.text)<100


def test_register_success_minimal(app_client):
    r = app_client.post(
        "/auth/register", json={"email": "alice1@ncsu.edu", "password": "Secret123!"}
    )
    assert r.status_code in (200, 201), r.text


def test_login_success_returns_token(app_client):
    # setup
    app_client.post(
        "/auth/register", json={"email": "alice2@ncsu.edu", "password": "Secret123!"}
    )
    # exercise
    r = app_client.post(
        "/auth/login", json={"email": "alice2@ncsu.edu", "password": "Secret123!"}
    )
    # verify
    assert r.status_code == 200, r.text
    assert r.json().get("token")


def test_me_returns_profile(app_client):
    # setup
    app_client.post(
        "/auth/register", json={"email": "alice3@ncsu.edu", "password": "Secret123!"}
    )
    r2 = app_client.post(
        "/auth/login", json={"email": "alice3@ncsu.edu", "password": "Secret123!"}
    )
    token = r2.json()["token"]
    # exercise
    r3 = app_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    # verify
    assert r3.status_code == 200, r3.text
    me = r3.json()
    assert me.get("id") is not None
    assert isinstance(me.get("points"), int)


def test_login_wrong_password(app_client):
    app_client.post(
        "/auth/register", json={"email": "bob@ncsu.edu", "password": "GoodPass1!"}
    )
    r = app_client.post(
        "/auth/login", json={"email": "bob@ncsu.edu", "password": "bad"}
    )
    assert r.status_code in (400, 401), r.text


def test_login_rejects_non_ncsu(app_client):
    # Even if account existed, backend enforces domain on login
    r = app_client.post(
        "/auth/login", json={"email": "user@gmail.com", "password": "x"}
    )
    assert r.status_code == 400
