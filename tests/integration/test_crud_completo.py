import pytest
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timezone, timedelta

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "fintech_logs_test"

RETENTION = {
    "AUTH": timedelta(days=365),
    "TRANSACTION": timedelta(days=365 * 3),
    "SECURITY": timedelta(days=90),
    "ERROR": timedelta(days=90),
    "AUDIT": timedelta(days=365 * 5),
    "ACCESS": timedelta(days=30),
}

LOG_AUTH = {
    "type": "AUTH",
    "severity": "INFO",
    "service": "auth-service",
    "correlation_id": "corr_integracion_001",
    "user_id": "usr_col_integracion",
    "detail": {
        "auth_method": "PIN",
        "result": "SUCCESS",
        "failed_attempts": 0,
        "device_id": "dev_test",
        "ip_address": "190.24.55.0",
        "city": "Bogota",
        "token_issued": True,
    },
}


@pytest.fixture
def col():
    mongo = MongoClient(MONGO_URL)
    db = mongo[DB_NAME]
    db["logs"].drop()
    yield db["logs"]
    db["logs"].drop()
    mongo.close()


def insertar_log(col, data):
    now = datetime.now(timezone.utc)
    doc = {**data, "timestamp": now, "expires_at": now + RETENTION[data["type"]]}
    result = col.insert_one(doc)
    return str(result.inserted_id)


@pytest.mark.integration
def test_crear_y_obtener_log(col):
    log_id = insertar_log(col, LOG_AUTH)
    found = col.find_one({"_id": ObjectId(log_id)})
    assert found is not None
    assert found["type"] == "AUTH"
    assert "expires_at" in found


@pytest.mark.integration
def test_filtro_por_tipo(col):
    insertar_log(col, LOG_AUTH)
    insertar_log(col, {**LOG_AUTH, "type": "TRANSACTION", "service": "pagos-service",
                       "detail": {"sub_type": "P2P", "amount_cop": 50000,
                                  "status": "APPROVED", "source_account": "nequi_****1234",
                                  "processing_time_ms": 200}})
    results = list(col.find({"type": "AUTH"}))
    assert len(results) == 1
    assert results[0]["type"] == "AUTH"


@pytest.mark.integration
def test_trazabilidad_correlation_id(col):
    corr = "corr_traza_integracion_001"
    insertar_log(col, {**LOG_AUTH, "correlation_id": corr})
    insertar_log(col, {**LOG_AUTH, "type": "TRANSACTION", "service": "pagos-service",
                       "correlation_id": corr,
                       "detail": {"sub_type": "P2P", "amount_cop": 100000,
                                  "status": "APPROVED", "source_account": "nequi_****5678",
                                  "processing_time_ms": 300}})
    results = list(col.find({"correlation_id": corr}).sort("timestamp", 1))
    assert len(results) == 2


@pytest.mark.integration
def test_actualizar_log(col):
    log_id = insertar_log(col, LOG_AUTH)
    col.update_one({"_id": ObjectId(log_id)}, {"$set": {"severity": "WARNING"}})
    updated = col.find_one({"_id": ObjectId(log_id)})
    assert updated["severity"] == "WARNING"


@pytest.mark.integration
def test_eliminar_log(col):
    log_id = insertar_log(col, LOG_AUTH)
    col.delete_one({"_id": ObjectId(log_id)})
    found = col.find_one({"_id": ObjectId(log_id)})
    assert found is None