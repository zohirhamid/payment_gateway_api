from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_test_merchant():
    response = client.post("/merchants/")
    assert response.status_code == 200
    return response.json()


def create_payment_intent(api_key: str):
    response = client.post(
        "/payment_intents/",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "amount": 1000,
            "currency": "gbp",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_webhook_event_created_after_confirm():
    merchant_data = create_test_merchant()
    api_key = merchant_data["api_key"]

    payment_intent = create_payment_intent(api_key)
    payment_intent_id = payment_intent["id"]

    confirm_response = client.post(
        f"/payment_intents/{payment_intent_id}/confirm",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert confirm_response.status_code == 200

    events_response = client.get("/webhooks/events")
    assert events_response.status_code == 200

    events = events_response.json()
    assert len(events) > 0

    latest_event = events[0]

    assert latest_event["payment_intent_id"] == payment_intent_id
    assert latest_event["event_type"] in ["payment.succeeded", "payment.failed"]
    assert latest_event["delivery_status"] in ["pending", "delivered", "failed"]