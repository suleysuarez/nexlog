import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from app.database import crear_indices
from app.routes.logs import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la app:
    - Al iniciar: crear índices en MongoDB (idempotente, seguro correrlo siempre).
    - Al cerrar: nada que limpiar (Motor cierra la conexión automáticamente).
    """
    await crear_indices()
    yield

app = FastAPI(
    title="NexLog API",
    description=(
        "Sistema de observabilidad y logging para Nequi (Bancolombia). "
        "Registra 6 tipos de eventos: AUTH, TRANSACTION, SECURITY, ERROR, AUDIT, ACCESS."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Todos los endpoints bajo /api/v1
app.include_router(router, prefix="/api/v1")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "nexlog")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

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
