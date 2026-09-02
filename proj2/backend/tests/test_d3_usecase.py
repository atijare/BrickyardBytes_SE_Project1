import uuid

import pytest

from conftest import auth_headers, register_and_login


MANUAL_E2E_REASON = "UI-only scenario; collect manual/e2e evidence for D3."


def unique_email(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8]}@ncsu.edu"


def create_run(
    client,
    token,
    restaurant="Port City Java",
    drop_point="Hunt Library",
    eta="12:30 PM",
    capacity=2,
):
    response = client.post(
        "/runs",
        headers=auth_headers(token),
        json={
            "restaurant": restaurant,
            "drop_point": drop_point,
            "eta": eta,
            "capacity": capacity,
        },
    )
    assert response.status_code in (200, 201), response.text
    return response.json()


@pytest.mark.xfail(
    strict=True,
    reason="Known defect: FoodRunCreate does not restrict drop points to campus.",
)
def test_uc4_rejects_off_campus_drop_location(app_client):
    token, _ = register_and_login(app_client, unique_email("uc4-off-campus"))

    response = app_client.post(
        "/runs",
        headers=auth_headers(token),
        json={
            "restaurant": "Port City Java",
            "drop_point": "Charlotte Douglas International Airport",
            "eta": "2:30 PM",
            "capacity": 2,
        },
    )

    assert response.status_code in (400, 422), response.text


@pytest.mark.parametrize("invalid_eta", ["2:85 PM", "25:00", "anything", ""])
@pytest.mark.xfail(
    strict=True,
    reason="Known defect: FoodRunCreate accepts malformed ETA strings.",
)
def test_uc4_rejects_invalid_eta(app_client, invalid_eta):
    token, _ = register_and_login(app_client, unique_email("uc4-invalid-eta"))

    response = app_client.post(
        "/runs",
        headers=auth_headers(token),
        json={
            "restaurant": "Port City Java",
            "drop_point": "Hunt Library",
            "eta": invalid_eta,
            "capacity": 2,
        },
    )

    assert response.status_code in (400, 422), response.text


def join_run(client, token, run_id, items="1x Coffee", amount=5.0, tip=0.0):
    return client.post(
        f"/runs/{run_id}/orders",
        headers=auth_headers(token),
        json={"items": items, "amount": amount, "tip": tip},
    )


def complete_run(client, token, run_id):
    return client.put(f"/runs/{run_id}/complete", headers=auth_headers(token))


def cancel_run(client, token, run_id):
    return client.put(f"/runs/{run_id}/cancel", headers=auth_headers(token))


def test_uc1_registers_with_valid_ncsu_email(app_client):
    response = app_client.post(
        "/auth/register",
        json={"email": unique_email("uc1-valid"), "password": "Secret123!"},
    )

    assert response.status_code in (200, 201), response.text
    assert response.json()["token"]


def test_uc1_rejects_already_existing_user(app_client):
    email = unique_email("uc1-duplicate")
    first = app_client.post(
        "/auth/register", json={"email": email, "password": "Secret123!"}
    )
    second = app_client.post(
        "/auth/register", json={"email": email, "password": "Different123!"}
    )

    assert first.status_code in (200, 201), first.text
    assert second.status_code == 409


def test_uc1_rejects_non_ncsu_email(app_client):
    response = app_client.post(
        "/auth/register",
        json={"email": "student@example.com", "password": "Secret123!"},
    )

    assert response.status_code == 400


def test_uc2_logs_in_with_correct_credentials(app_client):
    email = unique_email("uc2-valid")
    app_client.post("/auth/register", json={"email": email, "password": "Secret123!"})

    response = app_client.post(
        "/auth/login", json={"email": email, "password": "Secret123!"}
    )

    assert response.status_code == 200
    assert response.json()["token"]


def test_uc2_rejects_incorrect_password(app_client):
    email = unique_email("uc2-wrong-password")
    app_client.post("/auth/register", json={"email": email, "password": "Secret123!"})

    response = app_client.post(
        "/auth/login", json={"email": email, "password": "wrong-password"}
    )

    assert response.status_code == 401


def test_uc2_rejects_email_that_does_not_exist(app_client):
    response = app_client.post(
        "/auth/login",
        json={"email": unique_email("uc2-missing"), "password": "Secret123!"},
    )

    assert response.status_code == 401


@pytest.mark.skip(reason=MANUAL_E2E_REASON)
def test_uc3_broadcaster_home_page_loads_after_login_manual_e2e():
    pass


def test_uc3_broadcaster_can_view_and_interact_with_run_information(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc3-runner"))
    joiner_token, _ = register_and_login(app_client, unique_email("uc3-joiner"))
    run = create_run(app_client, runner_token, capacity=2)
    join = join_run(app_client, joiner_token, run["id"], items="2x Latte", amount=8.0)

    mine = app_client.get("/runs/mine", headers=auth_headers(runner_token))

    assert join.status_code in (200, 201), join.text
    assert mine.status_code == 200
    listed = next(item for item in mine.json() if item["id"] == run["id"])
    assert listed["orders"][0]["items"] == "2x Latte"
    assert "pin" not in listed["orders"][0]


def test_uc4_creates_broadcast_with_valid_information(app_client):
    token, _ = register_and_login(app_client, unique_email("uc4-valid"))

    run = create_run(app_client, token, restaurant="Talley Market")

    assert run["restaurant"] == "Talley Market"
    assert run["status"] == "active"


def test_uc4_rejects_broadcast_with_missing_or_invalid_information(app_client):
    token, _ = register_and_login(app_client, unique_email("uc4-invalid"))

    response = app_client.post(
        "/runs",
        headers=auth_headers(token),
        json={"restaurant": "Talley Market"},
    )

    assert response.status_code == 422


def test_uc5_views_active_runs(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc5-runner"))
    user_token, _ = register_and_login(app_client, unique_email("uc5-user"))
    run = create_run(app_client, runner_token, restaurant="Visible Active")

    response = app_client.get("/runs/available", headers=auth_headers(user_token))

    assert response.status_code == 200
    assert any(item["id"] == run["id"] for item in response.json())


def test_uc5_handles_case_where_created_runs_are_not_available(app_client):
    owner_token, _ = register_and_login(app_client, unique_email("uc5-owner"))
    viewer_token, _ = register_and_login(app_client, unique_email("uc5-viewer"))
    filler_token, _ = register_and_login(app_client, unique_email("uc5-filler"))
    own_run = create_run(app_client, viewer_token, restaurant="Own Hidden")
    full_run = create_run(app_client, owner_token, restaurant="Full Hidden", capacity=1)

    join_run(app_client, filler_token, full_run["id"])
    response = app_client.get("/runs/available", headers=auth_headers(viewer_token))
    ids = {item["id"] for item in response.json()}

    assert own_run["id"] not in ids
    assert full_run["id"] not in ids


def test_uc5_hides_cancelled_and_completed_runs_from_active_list(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc5-terminal"))
    user_token, _ = register_and_login(app_client, unique_email("uc5-terminal-user"))
    cancelled = create_run(app_client, runner_token, restaurant="Cancelled Hidden")
    completed = create_run(app_client, runner_token, restaurant="Completed Hidden")

    cancel_run(app_client, runner_token, cancelled["id"])
    complete_run(app_client, runner_token, completed["id"])
    response = app_client.get("/runs/available", headers=auth_headers(user_token))
    ids = {item["id"] for item in response.json()}

    assert cancelled["id"] not in ids
    assert completed["id"] not in ids


@pytest.mark.skip(reason=MANUAL_E2E_REASON)
def test_uc6_opens_or_uses_chatbot_before_login_manual_e2e():
    pass


def test_uc6_rejects_protected_ai_information_before_login(app_client):
    description = app_client.post(
        "/ai/run-description",
        json={"restaurant": "Talley", "drop_point": "Library", "eta": "1 PM"},
    )
    run_load = app_client.post(
        "/ai/run-load",
        json={"restaurant": "Talley", "capacity": 2, "orders": []},
    )

    assert description.status_code == 401
    assert run_load.status_code == 401


def test_uc7_returns_run_insights_after_login(app_client):
    token, _ = register_and_login(app_client, unique_email("uc7-user"))

    response = app_client.post(
        "/analytics/peak-forecast/run", headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert "peak_forecast" in response.json()


def test_uc7_handles_little_or_no_run_data_for_insights(app_client):
    token, _ = register_and_login(app_client, unique_email("uc7-empty"))

    response = app_client.post(
        "/analytics/peak-forecast/run", headers=auth_headers(token)
    )
    body = response.json()

    assert response.status_code == 200
    assert isinstance(body["hourly_timeseries"], list)
    assert isinstance(body["peak_forecast"], list)


def test_uc8_returns_alert_payload_after_login(app_client):
    token, _ = register_and_login(app_client, unique_email("uc8-user"))

    response = app_client.post(
        "/analytics/peak-forecast/run", headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert "rewards_issued" in response.json()
    assert "recent_rewards" in response.json()


def test_uc8_handles_no_alerts_without_fabricating_alerts(app_client):
    token, _ = register_and_login(app_client, unique_email("uc8-empty"))

    response = app_client.post(
        "/analytics/peak-forecast/run", headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json()["rewards_issued"] == []


def test_uc9_returns_broadcast_tips_after_login(app_client, monkeypatch):
    monkeypatch.setenv("AI_RUN_DESC_KEY", "")
    token, _ = register_and_login(app_client, unique_email("uc9-runner"))

    response = app_client.post(
        "/ai/run-description",
        headers=auth_headers(token),
        json={
            "restaurant": "Common Grounds",
            "drop_point": "EB2",
            "eta": "5 PM",
        },
    )

    assert response.status_code == 200
    suggestion = response.json()["suggestion"]
    assert "Common Grounds" in suggestion
    assert "EB2" in suggestion
    assert "5 PM" in suggestion
    assert len(suggestion.split()) >= 10
    assert "hardcoded" not in suggestion.lower()


def test_uc9_returns_tips_without_active_broadcast(app_client, monkeypatch):
    monkeypatch.setenv("AI_RUN_DESC_KEY", "")
    token, _ = register_and_login(app_client, unique_email("uc9-no-run"))

    response = app_client.post(
        "/ai/run-description",
        headers=auth_headers(token),
        json={
            "restaurant": "Atrium",
            "drop_point": "Library",
            "eta": "6 PM",
        },
    )

    assert response.status_code == 200
    assert "Atrium" in response.json()["suggestion"]


@pytest.mark.skip(reason=MANUAL_E2E_REASON)
def test_uc10_user_home_page_loads_after_login_manual_e2e():
    pass


def test_uc10_joins_eligible_run_from_home_page_data(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc10-runner"))
    user_token, _ = register_and_login(app_client, unique_email("uc10-user"))
    run = create_run(app_client, runner_token, capacity=2)

    available = app_client.get("/runs/available", headers=auth_headers(user_token))
    join = join_run(app_client, user_token, run["id"])
    joined = app_client.get("/runs/joined", headers=auth_headers(user_token))

    assert any(item["id"] == run["id"] for item in available.json())
    assert join.status_code in (200, 201), join.text
    assert any(item["id"] == run["id"] for item in joined.json())


def test_uc11_joins_active_broadcast(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc11-runner"))
    user_token, _ = register_and_login(app_client, unique_email("uc11-user"))
    run = create_run(app_client, runner_token)

    response = join_run(app_client, user_token, run["id"])

    assert response.status_code in (200, 201)


def test_uc11_unjoins_broadcast(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc11-unjoin-r"))
    user_token, _ = register_and_login(app_client, unique_email("uc11-unjoin-u"))
    run = create_run(app_client, runner_token)
    join_run(app_client, user_token, run["id"])

    response = app_client.delete(
        f"/runs/{run['id']}/orders/me", headers=auth_headers(user_token)
    )

    assert response.status_code == 200


def test_uc11_rejects_duplicate_join(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc11-dup-r"))
    user_token, _ = register_and_login(app_client, unique_email("uc11-dup-u"))
    run = create_run(app_client, runner_token, capacity=2)
    first = join_run(app_client, user_token, run["id"])
    second = join_run(app_client, user_token, run["id"])

    assert first.status_code in (200, 201)
    assert second.status_code == 400


def test_uc11_rejects_full_or_closed_broadcast_join(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc11-full-r"))
    first_token, _ = register_and_login(app_client, unique_email("uc11-full-a"))
    second_token, _ = register_and_login(app_client, unique_email("uc11-full-b"))
    run = create_run(app_client, runner_token, capacity=1)
    join_run(app_client, first_token, run["id"])

    response = join_run(app_client, second_token, run["id"])

    assert response.status_code == 400


def test_uc11_rejects_joining_own_run(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc11-self"))
    run = create_run(app_client, runner_token)

    response = join_run(app_client, runner_token, run["id"])

    assert response.status_code == 400


def test_uc12_checks_load_on_run_with_orders(app_client, monkeypatch):
    monkeypatch.setenv("AI_RUN_DESC_KEY", "")
    token, _ = register_and_login(app_client, unique_email("uc12-orders"))

    response = app_client.post(
        "/ai/run-load",
        headers=auth_headers(token),
        json={
            "restaurant": "Talley",
            "capacity": 2,
            "seats_remaining": 0,
            "orders": [{"items": "Party platter", "amount": 40.0}],
        },
    )

    assert response.status_code == 200
    assert "capacity" in response.json()["assessment"].lower()


def test_uc12_checks_load_on_run_with_no_orders(app_client, monkeypatch):
    monkeypatch.setenv("AI_RUN_DESC_KEY", "")
    token, _ = register_and_login(app_client, unique_email("uc12-empty"))

    response = app_client.post(
        "/ai/run-load",
        headers=auth_headers(token),
        json={
            "restaurant": "Talley",
            "capacity": 3,
            "seats_remaining": 3,
            "orders": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["assessment"] == "No orders yet; the run is currently light."


def test_uc13_creates_food_run_with_valid_information(app_client):
    token, _ = register_and_login(app_client, unique_email("uc13-valid"))

    run = create_run(app_client, token, restaurant="Atrium")

    assert run["restaurant"] == "Atrium"


def test_uc13_rejects_food_run_with_required_information_missing(app_client):
    token, _ = register_and_login(app_client, unique_email("uc13-missing"))

    response = app_client.post(
        "/runs", headers=auth_headers(token), json={"restaurant": "Atrium"}
    )

    assert response.status_code == 422


def test_uc13_rejects_food_run_creation_while_not_authenticated(app_client):
    response = app_client.post(
        "/runs",
        json={
            "restaurant": "Atrium",
            "drop_point": "Library",
            "eta": "2 PM",
            "capacity": 2,
        },
    )

    assert response.status_code == 401


def test_uc14_owner_cancels_active_food_run(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc14-owner"))
    run = create_run(app_client, runner_token)

    response = cancel_run(app_client, runner_token, run["id"])

    assert response.status_code == 200


def test_uc14_rejects_joining_cancelled_food_run(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc14-cancel-r"))
    joiner_token, _ = register_and_login(app_client, unique_email("uc14-cancel-u"))
    run = create_run(app_client, runner_token)
    cancel_run(app_client, runner_token, run["id"])

    response = join_run(app_client, joiner_token, run["id"])

    assert response.status_code == 400


def test_uc14_rejects_cancelling_another_users_run(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc14-runner"))
    other_token, _ = register_and_login(app_client, unique_email("uc14-other"))
    run = create_run(app_client, runner_token)

    response = cancel_run(app_client, other_token, run["id"])

    assert response.status_code == 403


def test_uc15_owner_completes_active_food_run(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc15-owner"))
    run = create_run(app_client, runner_token)

    response = complete_run(app_client, runner_token, run["id"])

    assert response.status_code == 200


def test_uc15_rejects_joining_completed_run(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc15-complete-r"))
    joiner_token, _ = register_and_login(app_client, unique_email("uc15-complete-u"))
    run = create_run(app_client, runner_token)
    complete_run(app_client, runner_token, run["id"])

    response = join_run(app_client, joiner_token, run["id"])

    assert response.status_code == 400


def test_uc15_rejects_completing_already_completed_run(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc15-repeat-r"))
    joiner_token, _ = register_and_login(app_client, unique_email("uc15-repeat-u"))
    run = create_run(app_client, runner_token)
    join_run(app_client, joiner_token, run["id"], amount=30.0)
    first = complete_run(app_client, runner_token, run["id"])
    points_after_first = app_client.get(
        "/points", headers=auth_headers(runner_token)
    ).json()["points"]

    second = complete_run(app_client, runner_token, run["id"])
    points_after_second = app_client.get(
        "/points", headers=auth_headers(runner_token)
    ).json()["points"]

    assert first.status_code == 200
    assert second.status_code == 400
    assert points_after_second == points_after_first


def test_uc16_redeems_points_with_sufficient_balance(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc16-redeem-r"))
    joiner_token, _ = register_and_login(app_client, unique_email("uc16-redeem-u"))
    run = create_run(app_client, runner_token)
    join_run(app_client, joiner_token, run["id"], amount=100.0)
    complete_run(app_client, runner_token, run["id"])

    response = app_client.post("/points/redeem", headers=auth_headers(runner_token))

    assert response.status_code == 200
    assert response.json()["remaining_points"] == 0


def test_uc16_rejects_redeeming_points_with_insufficient_balance(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc16-low"))

    response = app_client.post("/points/redeem", headers=auth_headers(runner_token))

    assert response.status_code == 400


def test_uc16_awards_points_after_completed_run(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc16-award-r"))
    joiner_token, _ = register_and_login(app_client, unique_email("uc16-award-u"))
    run = create_run(app_client, runner_token)
    join_run(app_client, joiner_token, run["id"], amount=100.0)

    complete_run(app_client, runner_token, run["id"])
    response = app_client.get("/points", headers=auth_headers(runner_token))

    assert response.status_code == 200
    assert response.json()["points"] >= 10


@pytest.mark.skip(reason=MANUAL_E2E_REASON)
def test_uc16_backend_redemption_behavior_matches_user_facing_ui_manual_e2e():
    pass


def test_uc17_cancels_or_unjoins_own_order(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc17-own-r"))
    user_token, _ = register_and_login(app_client, unique_email("uc17-own-u"))
    run = create_run(app_client, runner_token)
    join_run(app_client, user_token, run["id"])

    response = app_client.delete(
        f"/runs/{run['id']}/orders/me", headers=auth_headers(user_token)
    )

    assert response.status_code == 200


def test_uc17_rejects_cancelling_another_users_order(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc17-other-r"))
    owner_token, _ = register_and_login(app_client, unique_email("uc17-owner"))
    other_token, _ = register_and_login(app_client, unique_email("uc17-other"))
    run = create_run(app_client, runner_token)
    order = join_run(app_client, owner_token, run["id"]).json()

    response = app_client.delete(
        f"/runs/{run['id']}/orders/{order['id']}", headers=auth_headers(other_token)
    )

    assert response.status_code == 403


def test_uc17_rejects_cancelling_order_that_no_longer_exists(app_client):
    runner_token, _ = register_and_login(app_client, unique_email("uc17-missing-r"))
    user_token, _ = register_and_login(app_client, unique_email("uc17-missing-u"))
    run = create_run(app_client, runner_token)
    join_run(app_client, user_token, run["id"])
    first = app_client.delete(
        f"/runs/{run['id']}/orders/me", headers=auth_headers(user_token)
    )

    second = app_client.delete(
        f"/runs/{run['id']}/orders/me", headers=auth_headers(user_token)
    )

    assert first.status_code == 200
    assert second.status_code == 404


@pytest.mark.skip(reason=MANUAL_E2E_REASON)
def test_uc18_changes_profile_name_manual_e2e():
    pass


@pytest.mark.skip(reason=MANUAL_E2E_REASON)
def test_uc18_changes_password_manual_e2e():
    pass


@pytest.mark.skip(reason=MANUAL_E2E_REASON)
def test_uc18_changes_phone_number_manual_e2e():
    pass


@pytest.mark.skip(reason=MANUAL_E2E_REASON)
def test_uc18_changes_app_settings_or_preferences_manual_e2e():
    pass


@pytest.mark.skip(reason=MANUAL_E2E_REASON)
def test_uc18_rejects_invalid_profile_information_manual_e2e():
    pass


def test_uc19_answers_relevant_app_or_run_insight(app_client, monkeypatch):
    monkeypatch.setenv("AI_RUN_DESC_KEY", "")
    token, _ = register_and_login(app_client, unique_email("uc19-insight"))

    response = app_client.post(
        "/ai/run-load",
        headers=auth_headers(token),
        json={
            "restaurant": "Talley",
            "capacity": 2,
            "seats_remaining": 0,
            "orders": [{"items": "Party platter", "amount": 40.0}],
        },
    )

    assert response.status_code == 200
    assert response.json()["assessment"]


def test_uc19_handles_information_that_is_unavailable(app_client, monkeypatch):
    monkeypatch.setenv("AI_RUN_DESC_KEY", "")
    token, _ = register_and_login(app_client, unique_email("uc19-unavailable"))

    response = app_client.post(
        "/ai/run-load",
        headers=auth_headers(token),
        json={
            "restaurant": "Unknown Cafe",
            "capacity": 5,
            "seats_remaining": 5,
            "orders": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["assessment"] == "No orders yet; the run is currently light."


def test_uc19_does_not_invent_application_state(app_client, monkeypatch):
    monkeypatch.setenv("AI_RUN_DESC_KEY", "")
    token, _ = register_and_login(app_client, unique_email("uc19-no-hallucination"))

    response = app_client.post(
        "/ai/run-load",
        headers=auth_headers(token),
        json={
            "restaurant": "Unknown Cafe",
            "capacity": 5,
            "seats_remaining": 5,
            "orders": [],
        },
    )

    assert response.status_code == 200
    assert "No orders yet" in response.json()["assessment"]


def test_uc20_rejects_protected_feature_while_logged_out(app_client):
    owner_token, _ = register_and_login(app_client, unique_email("uc20-owner"))
    run = create_run(app_client, owner_token)

    response = app_client.put(f"/runs/{run['id']}/cancel")

    assert response.status_code == 401


def test_uc20_rejects_modifying_another_users_resource(app_client):
    owner_token, _ = register_and_login(app_client, unique_email("uc20-owner-auth"))
    attacker_token, _ = register_and_login(app_client, unique_email("uc20-attacker"))
    run = create_run(app_client, owner_token)

    response = cancel_run(app_client, attacker_token, run["id"])

    assert response.status_code == 403


def test_uc20_rejects_invalid_or_expired_authentication(app_client):
    response = app_client.get("/auth/me", headers={"Authorization": "Bearer invalid"})

    assert response.status_code in (401, 422)


def test_uc20_keeps_protected_state_unchanged_after_rejected_access(app_client):
    owner_token, _ = register_and_login(app_client, unique_email("uc20-state-owner"))
    attacker_token, _ = register_and_login(app_client, unique_email("uc20-state-attacker"))
    run = create_run(app_client, owner_token)

    logged_out = app_client.put(f"/runs/{run['id']}/cancel")
    unauthorized = cancel_run(app_client, attacker_token, run["id"])
    still_mine = app_client.get("/runs/mine", headers=auth_headers(owner_token))

    assert logged_out.status_code == 401
    assert unauthorized.status_code == 403
    assert any(item["id"] == run["id"] for item in still_mine.json())
