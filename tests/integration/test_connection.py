import os
from pymongo import MongoClient

def test_mongodb_connection():
    url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    client = MongoClient(url, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    client.close()
