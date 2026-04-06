from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_merchant_and_read_me():
    create_response = client.post("/merchants/")
    assert create_response.status_code == 200

    create_data = create_response.json()
    assert "id" in create_data
    assert "name" in create_data
    assert "api_key" in create_data

    api_key = create_data["api_key"]

    me_response = client.get(
        "/merchants/me",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert me_response.status_code == 200

    me_data = me_response.json()
    assert me_data["id"] == create_data["id"]
    assert me_data["name"] == create_data["name"]