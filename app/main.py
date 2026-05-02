import os
from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI(title="NexLog API")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "nexlog")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

@app.get("/health")
def health():
    try:
        client.admin.command("ping")
        return {
            "status": "ok",
            "service": "nexlog-api",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "nexlog-api",
            "database": str(e)
        }
