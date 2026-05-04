# app/models.py
from pydantic import BaseModel, Field
from typing import Any, Literal, Optional
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Política de retención por tipo — usada en POST para calcular expires_at
# Nunca se expone al cliente: la API lo gestiona internamente.
# ---------------------------------------------------------------------------
RETENTION: dict[str, timedelta] = {
    "ACCESS":      timedelta(days=30),
    "ERROR":       timedelta(days=90),
    "SECURITY":    timedelta(days=90),
    "AUTH":        timedelta(days=365),
    "TRANSACTION": timedelta(days=365 * 3),
    "AUDIT":       timedelta(days=365 * 5),
}

# Alias de tipos para reutilizar en modelos y routes
LogType = Literal["AUTH", "TRANSACTION", "SECURITY", "ERROR", "AUDIT", "ACCESS"]
Severity = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# ---------------------------------------------------------------------------
# LogCreate — cuerpo del POST /logs
# El cliente NO envía timestamp ni expires_at: la API los calcula.
# El campo detail es dict libre para soportar los 6 sub-esquemas sin bloquear
# al equipo mientras Persona 1 finaliza los esquemas exactos.
# ---------------------------------------------------------------------------
class LogCreate(BaseModel):
    type: LogType
    severity: Severity
    service: str
    correlation_id: str
    user_id: str
    detail: dict[str, Any]  # flexible — MongoDB acepta cualquier objeto


# ---------------------------------------------------------------------------
# LogResponse — lo que devuelve la API en GET y POST
# El alias _id → id convierte el ObjectId de Mongo a string legible.
# ---------------------------------------------------------------------------
class LogResponse(BaseModel):
    id: str = Field(alias="_id", serialization_alias="id")
    type: str
    severity: str
    timestamp: datetime
    service: str
    correlation_id: str
    user_id: str
    expires_at: datetime
    detail: dict[str, Any]

    model_config = {"populate_by_name": True, "by_alias": True}


# ---------------------------------------------------------------------------
# LogUpdate — cuerpo del PUT /logs/{id}
# Solo dos campos modificables: severity y detail.
# type, timestamp, correlation_id y expires_at son inmutables.
# NOTA: logs AUDIT no deberían actualizarse (requisito regulatorio);
# pendiente agregar validación 403 en PUT como mejora post-MVP.
# ---------------------------------------------------------------------------
class LogUpdate(BaseModel):
    severity: Optional[Severity] = None
    detail: Optional[dict[str, Any]] = None
