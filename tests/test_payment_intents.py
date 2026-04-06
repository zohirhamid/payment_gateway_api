from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_test_merchant():
    response = client.post("/merchants/")
    assert response.status_code == 200
    return response.json()


def test_create_payment_intent():
    merchant_data = create_test_merchant()
    api_key = merchant_data["api_key"]

    response = client.post(
        "/payment_intents/",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "amount": 1000,
            "currency": "gbp",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "id" in data
    assert data["merchant_id"] == merchant_data["id"]
    assert data["amount"] == 1000
    assert data["currency"] == "GBP"
    assert data["status"] == "requires_payment_method"

def test_get_payment_intent_by_id():
    merchant_data = create_test_merchant()
    api_key = merchant_data["api_key"]

    create_response = client.post(
        "/payment_intents/",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "amount": 1500,
            "currency": "usd",
        },
    )
    assert create_response.status_code == 200

    payment_intent = create_response.json()
    payment_intent_id = payment_intent["id"]

    get_response = client.get(
        f"/payment_intents/{payment_intent_id}",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert get_response.status_code == 200

    data = get_response.json()
    assert data["id"] == payment_intent_id
    assert data["merchant_id"] == merchant_data["id"]
    assert data["amount"] == 1500
    assert data["currency"] == "USD"
    assert data["status"] == "requires_payment_method"


def test_list_payment_intents():
    merchant_data = create_test_merchant()
    api_key = merchant_data["api_key"]

    first_response = client.post(
        "/payment_intents/",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "amount": 1000,
            "currency": "gbp",
        },
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/payment_intents/",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "amount": 2000,
            "currency": "usd",
        },
    )
    assert second_response.status_code == 200

    list_response = client.get(
        "/payment_intents/",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert list_response.status_code == 200

    data = list_response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    amounts = [item["amount"] for item in data]
    assert 1000 in amounts
    assert 2000 in amounts