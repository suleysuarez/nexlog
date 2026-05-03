from fastapi import FastAPI
from app.database import client

app = FastAPI(title="NexLog API")

@app.get("/health")
async def health():
    try:
        await client.admin.command("ping")
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
