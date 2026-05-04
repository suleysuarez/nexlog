# app/routes/logs.py
from fastapi import APIRouter, HTTPException, Query, Response
from app.models import LogCreate, LogResponse, LogUpdate, RETENTION
from app.database import get_collection
from datetime import datetime, timezone
from bson import ObjectId
from typing import Optional

router = APIRouter()


# ---------------------------------------------------------------------------
# Utilidad: serializar ObjectId → string para que Pydantic lo procese
# ---------------------------------------------------------------------------
def serialize_log(doc: dict) -> dict:
    """Convierte _id de ObjectId a string. Modifica el dict in-place y lo devuelve."""
    doc["_id"] = str(doc["_id"])
    return doc


def parse_object_id(log_id: str) -> ObjectId:
    """
    Intenta convertir el string del path a ObjectId.
    Lanza 400 si el formato es inválido (no son 24 hex chars).
    """
    try:
        return ObjectId(log_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="ID inválido — debe ser un ObjectId de MongoDB (24 caracteres hexadecimales)",
        )


# ===========================================================================
# ADVERTENCIA DE ORDEN: /logs/traza/{correlation_id} DEBE declararse ANTES
# que /logs/{log_id}. Si va después, FastAPI interpreta "traza" como un ID
# y devuelve 400 en vez de enrutar al endpoint correcto.
# ===========================================================================


# ---------------------------------------------------------------------------
# GET /api/v1/logs/traza/{correlation_id}
# Reconstruye el flujo completo de una operación en orden cronológico.
# Es el endpoint más valioso para el negocio — une todos los eventos de una
# misma transacción vía correlation_id.
# ---------------------------------------------------------------------------
@router.get("/logs/traza/{correlation_id}")
async def obtener_traza(correlation_id: str):
    col = get_collection()

    # Motor: find() es síncrono, devuelve cursor. sort() se encadena, to_list() es async.
    cursor = col.find({"correlation_id": correlation_id}).sort("timestamp", 1)
    logs = await cursor.to_list(length=None)

    if not logs:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron logs para correlation_id: {correlation_id}",
        )

    return {
        "correlation_id": correlation_id,
        "total_eventos": len(logs),
        "flujo": [serialize_log(log) for log in logs],
    }


# ---------------------------------------------------------------------------
# POST /api/v1/logs
# Crea un nuevo log. Calcula timestamp y expires_at internamente.
# El cliente NUNCA envía esos campos — la API los gestiona.
# ---------------------------------------------------------------------------
@router.post("/logs", response_model=LogResponse, status_code=201)
async def crear_log(log: LogCreate):
    col = get_collection()
    now = datetime.now(timezone.utc)

    documento = {
        "type":           log.type,
        "severity":       log.severity,
        "timestamp":      now,
        "service":        log.service,
        "correlation_id": log.correlation_id,
        "user_id":        log.user_id,
        "expires_at":     now + RETENTION[log.type],  # política interna, no del cliente
        "detail":         log.detail,
    }

    resultado = await col.insert_one(documento)
    creado = await col.find_one({"_id": resultado.inserted_id})
    return LogResponse(**serialize_log(creado))


# ---------------------------------------------------------------------------
# GET /api/v1/logs
# Lista logs con 7 filtros opcionales y paginación.
# Sin filtros devuelve todos los logs (paginados).
# Límite máximo: 100 docs por página para proteger la API.
# ---------------------------------------------------------------------------
@router.get("/logs")
async def listar_logs(
    type:           Optional[str]      = Query(None, description="Tipo de log: AUTH, TRANSACTION, SECURITY, ERROR, AUDIT, ACCESS"),
    service:        Optional[str]      = Query(None, description="Microservicio que generó el evento"),
    severity:       Optional[str]      = Query(None, description="Nivel de severidad: DEBUG, INFO, WARNING, ERROR, CRITICAL"),
    from_date:      Optional[datetime] = Query(None, description="Filtrar logs desde esta fecha (ISO 8601)"),
    to_date:        Optional[datetime] = Query(None, description="Filtrar logs hasta esta fecha (ISO 8601)"),
    user_id:        Optional[str]      = Query(None, description="ID del usuario o microservicio"),
    correlation_id: Optional[str]      = Query(None, description="ID de correlación para trazabilidad"),
    limit:          int                = Query(20, ge=1, le=100, description="Documentos por página (máx 100)"),
    skip:           int                = Query(0, ge=0,         description="Documentos a saltar para paginación"),
):
    col = get_collection()
    query: dict = {}

    # Construir el filtro dinámicamente — solo se agrega si el param llegó
    if type:           query["type"]           = type
    if service:        query["service"]        = service
    if severity:       query["severity"]       = severity
    if user_id:        query["user_id"]        = user_id
    if correlation_id: query["correlation_id"] = correlation_id

    # Filtro de rango de fechas — ambos son opcionales e independientes
    if from_date or to_date:
        query["timestamp"] = {}
        if from_date: query["timestamp"]["$gte"] = from_date
        if to_date:   query["timestamp"]["$lte"] = to_date

    total = await col.count_documents(query)
    cursor = col.find(query).sort("timestamp", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(length=limit)

    return {
        "total": total,
        "skip":  skip,
        "limit": limit,
        "data":  [serialize_log(log) for log in logs],
    }


# ---------------------------------------------------------------------------
# GET /api/v1/logs/{log_id}
# Detalle de un log por su _id de MongoDB.
# 400 si el ID no tiene formato ObjectId. 404 si no existe.
# ---------------------------------------------------------------------------
@router.get("/logs/{log_id}", response_model=LogResponse)
async def obtener_log(log_id: str):
    col = get_collection()
    object_id = parse_object_id(log_id)

    log = await col.find_one({"_id": object_id})
    if not log:
        raise HTTPException(status_code=404, detail=f"Log {log_id} no encontrado")

    return LogResponse(**serialize_log(log))


# ---------------------------------------------------------------------------
# PUT /api/v1/logs/{log_id}
# Actualiza severity y/o detail. Los demás campos son inmutables.
# 400 si no se enviaron campos. 404 si no existe.
# ---------------------------------------------------------------------------
@router.put("/logs/{log_id}", response_model=LogResponse)
async def actualizar_log(log_id: str, update: LogUpdate):
    col = get_collection()
    object_id = parse_object_id(log_id)

    # Solo actualizar los campos que llegaron con valor (excluir None)
    campos = {k: v for k, v in update.model_dump().items() if v is not None}
    if not campos:
        raise HTTPException(
            status_code=400,
            detail="No se enviaron campos para actualizar. Envía 'severity', 'detail' o ambos.",
        )

    resultado = await col.find_one_and_update(
        {"_id": object_id},
        {"$set": campos},
        return_document=True,  # devuelve el documento ya actualizado
    )

    if not resultado:
        raise HTTPException(status_code=404, detail=f"Log {log_id} no encontrado")

    return LogResponse(**serialize_log(resultado))


# ---------------------------------------------------------------------------
# DELETE /api/v1/logs/{log_id}
# Elimina un log por su _id. 204 si se eliminó. 404 si no existía.
# 204 No Content es el código correcto para DELETE exitoso.
# ---------------------------------------------------------------------------
@router.delete("/logs/{log_id}", status_code=204)
async def eliminar_log(log_id: str):
    col = get_collection()
    object_id = parse_object_id(log_id)

    resultado = await col.delete_one({"_id": object_id})
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Log {log_id} no encontrado")

    return Response(status_code=204)
