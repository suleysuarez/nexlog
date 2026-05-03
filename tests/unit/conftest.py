import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_db():
    with patch("app.main.db") as mock:
        mock.logs = MagicMock()
        mock.logs.insert_one = AsyncMock(return_value=MagicMock(inserted_id="fake_id"))
        mock.logs.find = MagicMock()
        mock.logs.find_one = AsyncMock(return_value=None)
        mock.logs.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        mock.logs.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        yield mock