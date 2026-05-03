# tests/unit/test_get_logs.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone


def fake_log(tipo: str = "AUTH", service: str = "auth-service") -> dict:
    return {
        "_id": ObjectId(),
        "type": tipo,
        "severity": "INFO",
        "timestamp": datetime.now(timezone.utc),
        "service": service,
        "correlation_id": "corr_test_001",
        "user_id": "usr_col_test",
        "expires_at": datetime.now(timezone.utc),
        "detail": {},
    }


def _build_col_mock(logs: list, total: int = None) -> MagicMock:
    """
    Mock correcto para colección Motor:
    - col.find() es síncrono → MagicMock base
    - cursor.to_list() es async → AsyncMock
    - col.count_documents() es async → AsyncMock
    """
    col = MagicMock()
    cursor_async = AsyncMock()
    cursor_async.to_list = AsyncMock(return_value=logs)
    col.find.return_value.sort.return_value.skip.return_value.limit.return_value = cursor_async
    col.count_documents = AsyncMock(return_value=total if total is not None else len(logs))
    return col


@pytest.mark.asyncio
async def test_get_logs_sin_filtros(client):
    logs = [fake_log("AUTH"), fake_log("TRANSACTION"), fake_log("ERROR")]
    with patch("app.routes.logs.get_collection") as mock_col:
        mock_col.return_value = _build_col_mock(logs, total=3)
        response = await client.get("/api/v1/logs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["data"]) == 3
    assert "skip" in data
    assert "limit" in data


@pytest.mark.asyncio
async def test_get_logs_filtro_type(client):
    logs = [fake_log("ERROR")]
    with patch("app.routes.logs.get_collection") as mock_col:
        col = _build_col_mock(logs, total=1)
        mock_col.return_value = col
        response = await client.get("/api/v1/logs?type=ERROR")
    assert response.status_code == 200
    call_args = col.find.call_args[0][0]
    assert call_args.get("type") == "ERROR"


@pytest.mark.asyncio
async def test_get_logs_filtro_service(client):
    logs = [fake_log("TRANSACTION", service="pagos-service")]
    with patch("app.routes.logs.get_collection") as mock_col:
        col = _build_col_mock(logs, total=1)
        mock_col.return_value = col
        response = await client.get("/api/v1/logs?service=pagos-service")
    assert response.status_code == 200
    call_args = col.find.call_args[0][0]
    assert call_args.get("service") == "pagos-service"


@pytest.mark.asyncio
async def test_get_logs_filtro_from_date(client):
    logs = [fake_log()]
    with patch("app.routes.logs.get_collection") as mock_col:
        col = _build_col_mock(logs, total=1)
        mock_col.return_value = col
        response = await client.get("/api/v1/logs?from_date=2025-01-01T00:00:00Z")
    assert response.status_code == 200
    call_args = col.find.call_args[0][0]
    assert "$gte" in call_args.get("timestamp", {})


@pytest.mark.asyncio
async def test_get_logs_filtro_rango_fechas(client):
    logs = [fake_log()]
    with patch("app.routes.logs.get_collection") as mock_col:
        col = _build_col_mock(logs, total=1)
        mock_col.return_value = col
        response = await client.get(
            "/api/v1/logs?from_date=2025-01-01T00:00:00Z&to_date=2025-12-31T23:59:59Z"
        )
    assert response.status_code == 200
    call_args = col.find.call_args[0][0]
    ts = call_args.get("timestamp", {})
    assert "$gte" in ts
    assert "$lte" in ts


@pytest.mark.asyncio
async def test_get_logs_paginacion(client):
    with patch("app.routes.logs.get_collection") as mock_col:
        mock_col.return_value = _build_col_mock([], total=100)
        response = await client.get("/api/v1/logs?limit=5&skip=10")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 5
    assert data["skip"] == 10


@pytest.mark.asyncio
async def test_get_logs_limit_excedido(client):
    response = await client.get("/api/v1/logs?limit=200")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_log_por_id_existe(client):
    fake_id = ObjectId()
    log = fake_log()
    log["_id"] = fake_id
    with patch("app.routes.logs.get_collection") as mock_col:
        col = AsyncMock()
        col.find_one = AsyncMock(return_value=log)
        mock_col.return_value = col
        response = await client.get(f"/api/v1/logs/{fake_id}")
    assert response.status_code == 200
    assert response.json()["type"] == "AUTH"


@pytest.mark.asyncio
async def test_get_log_por_id_no_existe(client):
    fake_id = str(ObjectId())
    with patch("app.routes.logs.get_collection") as mock_col:
        col = AsyncMock()
        col.find_one = AsyncMock(return_value=None)
        mock_col.return_value = col
        response = await client.get(f"/api/v1/logs/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_log_id_invalido(client):
    response = await client.get("/api/v1/logs/esto-no-es-un-objectid")
    assert response.status_code == 400
