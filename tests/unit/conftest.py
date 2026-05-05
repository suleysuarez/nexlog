import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

@pytest.fixture
def log_valido():
    return {
        "type": "AUTH",
        "severity": "INFO",
        "service": "auth-service",
        "correlation_id": "corr_nequi_test_001",
        "user_id": "usr_col_test_001",
        "detail": {
            "auth_method": "PIN",
            "result": "SUCCESS",
            "failed_attempts": 0,
            "device_id": "dev_and_test",
            "ip_address": "190.24.55.0",
            "city": "Bogota",
            "token_issued": True,
        },
    }