from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

def test_health():
    with patch("app.main.client") as mock_client:
        mock_client.admin.command = AsyncMock(return_value={"ok": 1})
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
