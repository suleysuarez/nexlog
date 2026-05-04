# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "fintech_logs")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


def get_collection():
    """Devuelve la colección 'logs'. Función separada para facilitar el mock en tests."""
    return db["logs"]


async def crear_indices():
    """
    Crea todos los índices necesarios al iniciar la app.
    - Índices simples para los filtros más comunes.
    - Índice TTL sobre expires_at para borrado automático por MongoDB.
    - Índice compuesto type+timestamp para el filtro más frecuente en k6.
    """
    col = get_collection()

    await col.create_index("timestamp", name="idx_timestamp")
    await col.create_index("type", name="idx_type")
    await col.create_index("service", name="idx_service")
    await col.create_index("user_id", name="idx_user_id")
    await col.create_index("correlation_id", name="idx_correlation_id")

    # TTL index: MongoDB elimina docs cuando expires_at < ahora
    await col.create_index(
        "expires_at",
        name="idx_ttl_expires_at",
        expireAfterSeconds=0,
    )

    # Índice compuesto para el filtro más usado: ?type=X ordenado por timestamp desc
    await col.create_index(
        [("type", 1), ("timestamp", -1)],
        name="idx_type_timestamp",
    )

    print("✅ Índices creados correctamente")
