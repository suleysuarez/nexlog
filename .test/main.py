# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
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


@app.get("/health", tags=["Infraestructura"])
async def health():
    """Endpoint de salud — usado por Docker healthcheck y CI/CD."""
    return {"status": "ok", "service": "nexlog-api"}
