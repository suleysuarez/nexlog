import pytest
import os
from pymongo import MongoClient

@pytest.fixture(scope="session")
def mongo_client():
    url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    client = MongoClient(url, serverSelectionTimeoutMS=3000)
    yield client
    client.close()

@pytest.fixture(scope="session")
def test_db(mongo_client):
    db = mongo_client["nexlog_test"]
    yield db
    db.client.drop_database("nexlog_test")