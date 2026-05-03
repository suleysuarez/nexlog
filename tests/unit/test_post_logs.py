# tests/unit/test_post_logs.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone


def _fake_doc(payload: dict, fake_id: ObjectId) -> dict:
    """Construye el documento que devolvería MongoDB después del insert."""
    return {
        **payload,
        "_id": fake_id,
        "timestamp": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc),
    }


# ---------------------------------------------------------------------------
# Caso exitoso — POST con datos válidos → 201 + campos calculados presentes
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_post_log_exitoso(client, log_valido):
    fake_id = ObjectId()
    fake_doc = _fake_doc(log_valido, fake_id)

    with patch("app.routes.logs.get_collection") as mock_col:
        col = AsyncMock()
        col.insert_one.return_value = MagicMock(inserted_id=fake_id)
        col.find_one.return_value = fake_doc
        mock_col.return_value = col

        response = await client.post("/api/v1/logs", json=log_valido)

    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "AUTH"
    assert data["severity"] == "INFO"
    assert data["service"] == "auth-service"
    assert "id" in data
    assert "timestamp" in data
    assert "expires_at" in data


# ---------------------------------------------------------------------------
# Tipo inválido → Pydantic rechaza antes de llegar a MongoDB → 422
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_post_log_tipo_invalido(client):
    datos = {
        "type": "PAGOS",
        "severity": "INFO",
        "service": "auth-service",
        "correlation_id": "corr_test",
        "user_id": "usr_test",
        "detail": {},
    }
    response = await client.post("/api/v1/logs", json=datos)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Severity inválida → 422
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_post_log_severity_invalida(client):
    datos = {
        "type": "AUTH",
        "severity": "ULTRA",
        "service": "auth-service",
        "correlation_id": "corr_test",
        "user_id": "usr_test",
        "detail": {},
    }
    response = await client.post("/api/v1/logs", json=datos)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Campo obligatorio faltante → 422
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_post_log_campo_faltante(client):
    sin_type = {
        "severity": "INFO",
        "service": "auth-service",
    }
    response = await client.post("/api/v1/logs", json=sin_type)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Detail vacío es válido — el campo es un dict libre
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_post_log_detail_vacio_es_valido(client, log_valido):
    fake_id = ObjectId()
    payload = {**log_valido, "detail": {}}
    fake_doc = _fake_doc(payload, fake_id)

    with patch("app.routes.logs.get_collection") as mock_col:
        col = AsyncMock()
        col.insert_one.return_value = MagicMock(inserted_id=fake_id)
        col.find_one.return_value = fake_doc
        mock_col.return_value = col

        response = await client.post("/api/v1/logs", json=payload)

    assert response.status_code == 201


# ---------------------------------------------------------------------------
# Verificar que el cliente NO puede inyectar expires_at — lo calcula la API
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_post_log_cliente_no_puede_inyectar_expires_at(client, log_valido):
    fake_id = ObjectId()
    fake_doc = _fake_doc(log_valido, fake_id)

    payload_con_expires = {**log_valido, "expires_at": "2099-01-01T00:00:00Z"}

    with patch("app.routes.logs.get_collection") as mock_col:
        col = AsyncMock()
        col.insert_one.return_value = MagicMock(inserted_id=fake_id)
        col.find_one.return_value = fake_doc
        mock_col.return_value = col

        response = await client.post("/api/v1/logs", json=payload_con_expires)

    assert response.status_code == 201
    assert response.json()["expires_at"] != "2099-01-01T00:00:00Z"
