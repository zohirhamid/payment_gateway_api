from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_test_merchant():
    response = client.post("/merchants/")
    assert response.status_code == 200
    return response.json()


def test_create_payment_intent_idempotent_same_key_same_payload():
    merchant_data = create_test_merchant()
    api_key = merchant_data["api_key"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Idempotency-Key": "create-pi-123",
    }

    payload = {
        "amount": 1000,
        "currency": "gbp",
    }

    first_response = client.post(
        "/payment_intents/",
        headers=headers,
        json=payload,
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/payment_intents/",
        headers=headers,
        json=payload,
    )
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["id"] == second_data["id"]
    assert first_data["merchant_id"] == second_data["merchant_id"]
    assert first_data["amount"] == second_data["amount"]
    assert first_data["currency"] == second_data["currency"]
    assert first_data["status"] == second_data["status"]


def test_create_payment_intent_idempotent_same_key_different_payload():
    merchant_data = create_test_merchant()
    api_key = merchant_data["api_key"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Idempotency-Key": "create-pi-456",
    }

    first_response = client.post(
        "/payment_intents/",
        headers=headers,
        json={
            "amount": 1000,
            "currency": "gbp",
        },
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/payment_intents/",
        headers=headers,
        json={
            "amount": 2000,
            "currency": "gbp",
        },
    )
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Idempotency key was already used with a different payload."
    )

def create_payment_intent(api_key: str, amount: int = 1000, currency: str = "gbp"):
    response = client.post(
        "/payment_intents/",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "amount": amount,
            "currency": currency,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_confirm_payment_intent_idempotent_same_key_same_request():
    merchant_data = create_test_merchant()
    api_key = merchant_data["api_key"]

    payment_intent = create_payment_intent(api_key=api_key)
    payment_intent_id = payment_intent["id"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Idempotency-Key": "confirm-pi-123",
    }

    first_response = client.post(
        f"/payment_intents/{payment_intent_id}/confirm",
        headers=headers,
    )
    assert first_response.status_code == 200

    second_response = client.post(
        f"/payment_intents/{payment_intent_id}/confirm",
        headers=headers,
    )
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["payment_intent_id"] == second_data["payment_intent_id"]
    assert first_data["charge_id"] == second_data["charge_id"]
    assert first_data["status"] == second_data["status"]


def test_confirm_payment_intent_second_call_with_different_key_returns_409():
    merchant_data = create_test_merchant()
    api_key = merchant_data["api_key"]

    payment_intent = create_payment_intent(api_key=api_key)
    payment_intent_id = payment_intent["id"]

    first_response = client.post(
        f"/payment_intents/{payment_intent_id}/confirm",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Idempotency-Key": "confirm-pi-456-a",
        },
    )
    assert first_response.status_code == 200

    second_response = client.post(
        f"/payment_intents/{payment_intent_id}/confirm",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Idempotency-Key": "confirm-pi-456-b",
        },
    )
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Payment intent has already been processed or is not confirmable."
    )