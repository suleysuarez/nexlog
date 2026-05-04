# tests/unit/test_put_delete_traza_logs.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone


def fake_log_doc(severity: str = "INFO") -> dict:
    return {
        "_id": ObjectId(),
        "type": "AUTH",
        "severity": severity,
        "timestamp": datetime.now(timezone.utc),
        "service": "auth-service",
        "correlation_id": "corr_test_put",
        "user_id": "usr_test",
        "expires_at": datetime.now(timezone.utc),
        "detail": {"auth_method": "PIN"},
    }


# ===========================================================================
# PUT /logs/{id}
# ===========================================================================

@pytest.mark.asyncio
async def test_put_log_exitoso_severity(client):
    """PUT actualizando severity → 200 con el valor nuevo."""
    fake_id = str(ObjectId())
    doc_actualizado = fake_log_doc(severity="WARNING")

    with patch("app.routes.logs.get_collection") as mock_col:
        col = AsyncMock()
        col.find_one_and_update.return_value = doc_actualizado
        mock_col.return_value = col

        response = await client.put(f"/api/v1/logs/{fake_id}", json={"severity": "WARNING"})

    assert response.status_code == 200
    assert response.json()["severity"] == "WARNING"


@pytest.mark.asyncio
async def test_put_log_exitoso_detail(client):
    """PUT actualizando detail → 200."""
    fake_id = str(ObjectId())
    doc_actualizado = fake_log_doc()
    doc_actualizado["detail"] = {"auth_method": "FACIAL_BIOMETRICS"}

    with patch("app.routes.logs.get_collection") as mock_col:
        col = AsyncMock()
        col.find_one_and_update.return_value = doc_actualizado
        mock_col.return_value = col

        response = await client.put(
            f"/api/v1/logs/{fake_id}",
            json={"detail": {"auth_method": "FACIAL_BIOMETRICS"}},
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_put_log_sin_campos_devuelve_400(client):
    """PUT sin campos → 400 (no hay nada que actualizar)."""
    fake_id = str(ObjectId())
    response = await client.put(f"/api/v1/logs/{fake_id}", json={})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_put_log_no_existe_devuelve_404(client):
    """PUT sobre ID que no existe → 404."""
    fake_id = str(ObjectId())

    with patch("app.routes.logs.get_collection") as mock_col:
        col = AsyncMock()
        col.find_one_and_update.return_value = None
        mock_col.return_value = col

        response = await client.put(f"/api/v1/logs/{fake_id}", json={"severity": "ERROR"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_put_log_id_invalido_devuelve_400(client):
    """PUT con ID malformado → 400."""
    response = await client.put("/api/v1/logs/id-invalido", json={"severity": "ERROR"})
    assert response.status_code == 400


# ===========================================================================
# DELETE /logs/{id}
# ===========================================================================

@pytest.mark.asyncio
async def test_delete_log_exitoso(client):
    """DELETE de log existente → 204 sin cuerpo."""
    fake_id = str(ObjectId())

    with patch("app.routes.logs.get_collection") as mock_col:
        col = AsyncMock()
        col.delete_one.return_value = MagicMock(deleted_count=1)
        mock_col.return_value = col

        response = await client.delete(f"/api/v1/logs/{fake_id}")

    assert response.status_code == 204
    assert response.content == b""  # 204 no tiene cuerpo


@pytest.mark.asyncio
async def test_delete_log_no_existe_devuelve_404(client):
    """DELETE de ID que no existe → 404."""
    fake_id = str(ObjectId())

    with patch("app.routes.logs.get_collection") as mock_col:
        col = AsyncMock()
        col.delete_one.return_value = MagicMock(deleted_count=0)
        mock_col.return_value = col

        response = await client.delete(f"/api/v1/logs/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_log_id_invalido_devuelve_400(client):
    """DELETE con ID malformado → 400."""
    response = await client.delete("/api/v1/logs/no-es-un-objectid")
    assert response.status_code == 400


# ===========================================================================
# GET /logs/traza/{correlation_id}
# ===========================================================================

@pytest.mark.asyncio
async def test_traza_devuelve_logs_ordenados(client):
    """GET traza → total_eventos correcto y flujo con todos los logs."""
    corr = "corr_nequi_traza_test"
    logs = [
        {**fake_log_doc(), "_id": ObjectId(), "correlation_id": corr, "type": "AUTH"},
        {**fake_log_doc(), "_id": ObjectId(), "correlation_id": corr, "type": "TRANSACTION"},
        {**fake_log_doc(), "_id": ObjectId(), "correlation_id": corr, "type": "AUDIT"},
    ]

    with patch("app.routes.logs.get_collection") as mock_col:
        col = MagicMock()  # síncrono para que find() no sea coroutine
        cursor_async = AsyncMock()
        cursor_async.to_list = AsyncMock(return_value=logs)
        col.find.return_value.sort.return_value = cursor_async
        mock_col.return_value = col

        response = await client.get(f"/api/v1/logs/traza/{corr}")

    assert response.status_code == 200
    data = response.json()
    assert data["correlation_id"] == corr
    assert data["total_eventos"] == 3
    assert len(data["flujo"]) == 3


@pytest.mark.asyncio
async def test_traza_correlation_id_inexistente_devuelve_404(client):
    """GET traza con correlation_id que no tiene logs → 404."""
    with patch("app.routes.logs.get_collection") as mock_col:
        col = MagicMock()
        cursor_async = AsyncMock()
        cursor_async.to_list = AsyncMock(return_value=[])
        col.find.return_value.sort.return_value = cursor_async
        mock_col.return_value = col

        response = await client.get("/api/v1/logs/traza/corr_inexistente_xyz")

    assert response.status_code == 404
