import pytest
import os
from pymongo import MongoClient

@pytest.mark.integration
def test_mongodb_connection(mongo_client):
    result = mongo_client.admin.command("ping")
    assert result["ok"] == 1

@pytest.mark.integration
def test_database_exists(test_db):
    collections = test_db.list_collection_names()
    assert isinstance(collections, list)

@pytest.mark.integration
def test_insert_and_find_log(test_db):
    log = {
        "type": "AUTH",
        "severity": "INFO",
        "service": "auth-service",
        "user_id": "usr_test_001",
        "correlation_id": "corr_test_001",
        "detail": {
            "auth_method": "PIN",
            "result": "SUCCESS",
            "failed_attempts": 0,
            "city": "Bogota"
        }
    }
    result = test_db.logs.insert_one(log)
    assert result.inserted_id is not None

    found = test_db.logs.find_one({"correlation_id": "corr_test_001"})
    assert found is not None
    assert found["type"] == "AUTH"