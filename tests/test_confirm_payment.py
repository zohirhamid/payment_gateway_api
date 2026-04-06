from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_test_merchant():
    response = client.post("/merchants/")
    assert response.status_code == 200
    return response.json()


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


def test_confirm_payment_intent_once_only():
    merchant_data = create_test_merchant()
    api_key = merchant_data["api_key"]

    payment_intent = create_payment_intent(api_key=api_key)
    payment_intent_id = payment_intent["id"]

    first_confirm_response = client.post(
        f"/payment_intents/{payment_intent_id}/confirm",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert first_confirm_response.status_code == 200

    first_confirm_data = first_confirm_response.json()
    assert first_confirm_data["payment_intent_id"] == payment_intent_id
    assert "charge_id" in first_confirm_data
    assert first_confirm_data["status"] in ["succeeded", "failed"]

    second_confirm_response = client.post(
        f"/payment_intents/{payment_intent_id}/confirm",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert second_confirm_response.status_code == 409
    assert second_confirm_response.json()["detail"] == (
        "Payment intent has already been processed or is not confirmable."
    )