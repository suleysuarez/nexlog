import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_ok():
    with patch("app.main.client") as mock_client:
        mock_client.admin.command = AsyncMock(return_value={"ok": 1})
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["database"] == "connected"

def test_health_db_down():
    with patch("app.main.client") as mock_client:
        mock_client.admin.command = AsyncMock(side_effect=Exception("Connection refused"))
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "error"

def test_health_service_name():
    with patch("app.main.client") as mock_client:
        mock_client.admin.command = AsyncMock(return_value={"ok": 1})
        response = client.get("/health")
        assert response.json()["service"] == "nexlog-api"