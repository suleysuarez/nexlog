"""
seed_fintech_logs.py
Módulo L03 — Poblado de datos para fintech_logs (MongoDB)
Sistema de logs Nequi · 9.000 documentos realistas
Ejecutar: python seed_fintech_logs.py
"""

import random
import uuid
from datetime import datetime, timedelta

from faker import Faker
from pymongo import MongoClient, ASCENDING, InsertOne
from pymongo.errors import BulkWriteError

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
MONGO_URI = "mongodb://localhost:27017"
DB_NAME   = "fintech_logs"
COL_NAME  = "logs"
TOTAL     = 9_000
BATCH_SIZE = 500          # inserciones por lote (bulk_write)

fake = Faker("es_CO")
random.seed(42)

# ─── CATÁLOGOS DE NEGOCIO (contexto Nequi / Colombia) ─────────────────────────
SERVICIOS = [
    "auth-service", "pagos-service", "transferencias-service",
    "recarga-service", "retiros-service", "fraude-service",
    "notificaciones-service", "kyc-service", "gateway-pse",
    "gateway-ach", "api-gateway", "sesiones-service",
]

VERSIONES_APP = ["4.18.0", "4.19.1", "4.20.0", "4.21.3", "5.0.0", "5.1.2"]

CIUDADES_CO = [
    "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena",
    "Bucaramanga", "Pereira", "Manizales", "Cúcuta", "Ibagué",
    "Santa Marta", "Villavicencio", "Pasto", "Montería", "Neiva",
]

OPERADORES_CO = ["Claro", "Movistar", "Tigo", "WOM", "ETB"]

DISPOSITIVOS = [
    "Samsung Galaxy S23", "Samsung Galaxy A54", "Xiaomi Redmi Note 12",
    "iPhone 14", "iPhone 13", "Motorola Edge 40", "Huawei P50",
    "OPPO A78", "Realme 11 Pro", "iPhone 12",
]

SISTEMAS_OS = ["Android 13", "Android 14", "iOS 16.5", "iOS 17.0", "Android 12"]

METODOS_PAGO = ["PSE", "ACH", "NEQUI_P2P", "QR_PAGO", "LINK_COBRO"]

TIPOS_TRANSACCION = [
    "TRANSFERENCIA_P2P", "RECARGA_CELULAR", "PAGO_SERVICIOS",
    "RETIRO_ATM", "PAGO_QR", "ENVIO_INTERNACIONAL",
]

ERRORES_TECNICOS = [
    "ConnectionTimeout", "MongoDBUnavailable", "PSEGatewayError",
    "ACHRejected", "TokenExpired", "RateLimitExceeded",
    "NullPointerException", "InvalidJWTSignature", "CircuitBreakerOpen",
]

ACCIONES_AUDIT = [
    "ACTUALIZAR_LIMITE_TRANSACCION", "CAMBIO_PIN", "MODIFICAR_DATOS_PERSONALES",
    "ACTIVAR_CUENTA", "DESACTIVAR_CUENTA", "CAMBIO_NUMERO_CELULAR",
    "ACTUALIZAR_DATOS_BANCARIOS", "RESTABLECER_CONTRASENA",
]

ALERTAS_SEGURIDAD = [
    "INTENTOS_LOGIN_EXCESIVOS", "IP_LISTA_NEGRA", "PATRON_FRAUDE_DETECTADO",
    "DISPOSITIVO_NO_RECONOCIDO", "GEOLOCALIZACION_SOSPECHOSA",
    "TRANSACCION_MONTO_INUSUAL", "MULTIPLE_SESION_ACTIVA",
]

METODOS_HTTP = ["GET", "POST", "PUT", "DELETE", "PATCH"]

ENDPOINTS_API = [
    "/api/v1/transferencias", "/api/v1/recargas", "/api/v1/pagos",
    "/api/v1/auth/login", "/api/v1/auth/logout", "/api/v1/usuarios/perfil",
    "/api/v1/retiros", "/api/v1/historial", "/api/v1/qr/generar",
]

# ─── GENERADORES DE CORRELATION_ID ────────────────────────────────────────────
def nuevo_correlation_id() -> str:
    return f"corr_nequi_{uuid.uuid4().hex[:16]}"

# ─── TIMESTAMP ALEATORIO (últimos 90 días) ────────────────────────────────────
def timestamp_aleatorio() -> datetime:
    delta = timedelta(
        days=random.randint(0, 90),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return datetime.utcnow() - delta

# ─── CAMPO BASE COMÚN ─────────────────────────────────────────────────────────
def base_log(tipo: str, severidad: str, servicio: str, correlation_id: str) -> dict:
    return {
        "tipo":           tipo,
        "severidad":      severidad,
        "timestamp":      timestamp_aleatorio(),
        "servicio":       servicio,
        "correlation_id": correlation_id,
        "usuario_id":     f"usr_{uuid.uuid4().hex[:10]}",
        "version_app":    random.choice(VERSIONES_APP),
    }

# ─── GENERADORES DE DETALLE POR TIPO ──────────────────────────────────────────
def detalle_auth() -> dict:
    metodo = random.choice(["PIN", "BIOMETRIA", "OTP_SMS", "FACE_ID"])
    exitoso = random.random() > 0.15
    return {
        "metodo_autenticacion": metodo,
        "exitoso":              exitoso,
        "intentos_fallidos":    0 if exitoso else random.randint(1, 5),
        "dispositivo":          random.choice(DISPOSITIVOS),
        "sistema_operativo":    random.choice(SISTEMAS_OS),
        "ciudad":               random.choice(CIUDADES_CO),
        "operador":             random.choice(OPERADORES_CO),
        "token_generado":       exitoso,
        "sesion_id":            f"ses_{uuid.uuid4().hex[:12]}" if exitoso else None,
        "razon_fallo":          None if exitoso else random.choice([
            "PIN_INCORRECTO", "BIOMETRIA_NO_COINCIDE", "OTP_EXPIRADO"
        ]),
    }

def detalle_transaction() -> dict:
    tipo_tx = random.choice(TIPOS_TRANSACCION)
    monto   = round(random.uniform(1_000, 5_000_000), 0)
    exitosa = random.random() > 0.08
    return {
        "tipo_transaccion":   tipo_tx,
        "monto_cop":          monto,
        "metodo_pago":        random.choice(METODOS_PAGO),
        "ciudad_origen":      random.choice(CIUDADES_CO),
        "ciudad_destino":     random.choice(CIUDADES_CO),
        "exitosa":            exitosa,
        "codigo_referencia":  f"REF{random.randint(100000000, 999999999)}",
        "tiempo_procesamiento_ms": random.randint(80, 4500),
        "canal":              random.choice(["APP_MOVIL", "USSD", "WEB"]),
        "razon_fallo":        None if exitosa else random.choice([
            "SALDO_INSUFICIENTE", "CUENTA_DESTINO_INVALIDA",
            "LIMITE_DIARIO_EXCEDIDO", "PSE_NO_DISPONIBLE",
        ]),
    }

def detalle_security() -> dict:
    nivel_riesgo = random.choice(["BAJO", "MEDIO", "ALTO", "CRITICO"])
    return {
        "tipo_alerta":        random.choice(ALERTAS_SEGURIDAD),
        "nivel_riesgo":       nivel_riesgo,
        "accion_tomada":      random.choice([
            "BLOQUEO_TEMPORAL", "NOTIFICACION_USUARIO",
            "REQUIERE_VERIFICACION", "BLOQUEO_PERMANENTE", "MONITOREO_ACTIVO",
        ]),
        "ciudad":             random.choice(CIUDADES_CO),
        "dispositivo":        random.choice(DISPOSITIVOS),
        "bloqueo_aplicado":   nivel_riesgo in ["ALTO", "CRITICO"],
        "revisado_por":       f"analista_{random.randint(1, 20):03d}" if nivel_riesgo == "CRITICO" else None,
    }

def detalle_error() -> dict:
    return {
        "tipo_error":         random.choice(ERRORES_TECNICOS),
        "mensaje":            fake.sentence(nb_words=8),
        "stack_trace_hash":   uuid.uuid4().hex[:32],
        "endpoint_afectado":  random.choice(ENDPOINTS_API),
        "tiempo_respuesta_ms": random.randint(3000, 30000),
        "reintentos":         random.randint(0, 3),
        "resuelto":           random.random() > 0.4,
        "codigo_http":        random.choice([500, 502, 503, 504, 429]),
    }

def detalle_audit() -> dict:
    return {
        "accion":             random.choice(ACCIONES_AUDIT),
        "dato_modificado":    random.choice([
            "limite_transaccion_diario", "numero_celular_hash",
            "datos_personales", "estado_cuenta", "pin_hash",
        ]),
        "valor_anterior_hash": uuid.uuid4().hex[:32],
        "valor_nuevo_hash":    uuid.uuid4().hex[:32],
        "motivo":             fake.sentence(nb_words=6),
        "ip_origen_hash":     uuid.uuid4().hex[:16],   # IP hasheada, no en texto plano
        "aprobado_por":       f"supervisor_{random.randint(1, 10):02d}",
        "canal_solicitud":    random.choice(["APP_MOVIL", "CALL_CENTER", "OFICINA"]),
        "cumple_sfc_029":     True,   # campo de trazabilidad regulatoria obligatorio
    }

def detalle_access() -> dict:
    codigo = random.choices(
        [200, 201, 400, 401, 403, 404, 429, 500, 503],
        weights=[50, 10, 10, 8, 5, 7, 3, 5, 2],
        k=1
    )[0]
    return {
        "metodo_http":        random.choice(METODOS_HTTP),
        "endpoint":           random.choice(ENDPOINTS_API),
        "codigo_respuesta":   codigo,
        "tiempo_respuesta_ms": random.randint(20, 2500),
        "bytes_respuesta":    random.randint(128, 65536),
        "user_agent":         f"NequiApp/{random.choice(VERSIONES_APP)} ({random.choice(SISTEMAS_OS)})",
        "ip_hash":            uuid.uuid4().hex[:16],   # IP hasheada
        "exitoso":            codigo < 400,
    }

# ─── MAPA DE CONFIGURACIÓN POR TIPO ───────────────────────────────────────────
TIPO_CONFIG = {
    "AUTH": {
        "cantidad":   1_800,
        "severidades": ["INFO"] * 70 + ["WARNING"] * 20 + ["ERROR"] * 10,
        "servicios":  ["auth-service", "sesiones-service", "kyc-service"],
        "detalle_fn": detalle_auth,
    },
    "TRANSACTION": {
        "cantidad":   2_250,
        "severidades": ["INFO"] * 60 + ["WARNING"] * 25 + ["ERROR"] * 15,
        "servicios":  ["pagos-service", "transferencias-service", "gateway-pse", "gateway-ach"],
        "detalle_fn": detalle_transaction,
    },
    "SECURITY": {
        "cantidad":   540,
        "severidades": ["WARNING"] * 40 + ["ERROR"] * 35 + ["CRITICAL"] * 25,
        "servicios":  ["fraude-service", "auth-service", "api-gateway"],
        "detalle_fn": detalle_security,
    },
    "ERROR": {
        "cantidad":   900,
        "severidades": ["ERROR"] * 60 + ["CRITICAL"] * 25 + ["WARNING"] * 15,
        "servicios":  SERVICIOS,
        "detalle_fn": detalle_error,
    },
    "AUDIT": {
        "cantidad":   360,
        "severidades": ["INFO"] * 50 + ["WARNING"] * 30 + ["ERROR"] * 20,
        "servicios":  ["kyc-service", "auth-service", "sesiones-service"],
        "detalle_fn": detalle_audit,
    },
    "ACCESS": {
        "cantidad":   3_150,
        "severidades": ["DEBUG"] * 20 + ["INFO"] * 65 + ["WARNING"] * 10 + ["ERROR"] * 5,
        "servicios":  ["api-gateway"] + SERVICIOS,
        "detalle_fn": detalle_access,
    },
}

# ─── GENERACIÓN DE OPERACIONES ENCADENADAS (trazabilidad) ─────────────────────
# Se generan 300 correlation_ids compartidos para simular operaciones reales
# donde múltiples logs pertenecen a la misma transacción.
POOL_CORRELATION = [nuevo_correlation_id() for _ in range(300)]

def obtener_correlation_id() -> str:
    """70% de probabilidad de reutilizar un ID del pool (trazabilidad real)."""
    if random.random() < 0.70:
        return random.choice(POOL_CORRELATION)
    return nuevo_correlation_id()

# ─── GENERACIÓN DE DOCUMENTOS ─────────────────────────────────────────────────
def generar_documentos() -> list:
    docs = []
    for tipo, cfg in TIPO_CONFIG.items():
        for _ in range(cfg["cantidad"]):
            severidad = random.choice(cfg["severidades"])
            servicio  = random.choice(cfg["servicios"])
            corr_id   = obtener_correlation_id()
            doc = base_log(tipo, severidad, servicio, corr_id)
            doc["detalle"] = cfg["detalle_fn"]()
            docs.append(doc)
    random.shuffle(docs)   # romper el orden por tipo
    return docs

# ─── INSERCIÓN EN LOTES ───────────────────────────────────────────────────────
def insertar_en_lotes(coleccion, documentos: list):
    total_insertados = 0
    for i in range(0, len(documentos), BATCH_SIZE):
        lote = documentos[i : i + BATCH_SIZE]
        operaciones = [InsertOne(doc) for doc in lote]
        try:
            resultado = coleccion.bulk_write(operaciones, ordered=False)
            total_insertados += resultado.inserted_count
            print(f"  Lote {i // BATCH_SIZE + 1:>3} — {total_insertados:>6} / {len(documentos)} insertados")
        except BulkWriteError as bwe:
            print(f"  ⚠ Error en lote {i // BATCH_SIZE + 1}: {bwe.details['nInserted']} insertados parcialmente")
    return total_insertados

# ─── CREAR ÍNDICES ────────────────────────────────────────────────────────────
def crear_indices(coleccion):
    print("\n📑 Creando índices...")
    coleccion.create_index([("timestamp", ASCENDING)],  name="idx_timestamp")
    coleccion.create_index([("tipo",      ASCENDING)],  name="idx_tipo")
    coleccion.create_index([("servicio",  ASCENDING)],  name="idx_servicio")
    coleccion.create_index([("usuario_id",ASCENDING)],  name="idx_usuario_id")
    coleccion.create_index([("correlation_id", ASCENDING)], name="idx_correlation_id")
    print("   ✓ 5 índices creados (timestamp, tipo, servicio, usuario_id, correlation_id)")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("═" * 60)
    print("  NexLog — Seeding 9.000 documentos en fintech_logs")
    print("═" * 60)

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        print(f"✓ Conectado a MongoDB: {MONGO_URI}\n")
    except Exception as e:
        print(f"✗ No se pudo conectar a MongoDB: {e}")
        print("  Verifica que MongoDB esté corriendo en localhost:27017")
        return

    db  = client[DB_NAME]
    col = db[COL_NAME]

    existentes = col.count_documents({})
    if existentes > 0:
        respuesta = input(f"  La colección ya tiene {existentes} documentos. ¿Agregar más? [s/N]: ")
        if respuesta.strip().lower() != "s":
            print("  Operación cancelada.")
            return

    print(f"⚙  Generando {TOTAL} documentos...")
    documentos = generar_documentos()
    print(f"   ✓ {len(documentos)} documentos generados en memoria\n")

    print(f"💾 Insertando en lotes de {BATCH_SIZE}:")
    total = insertar_en_lotes(col, documentos)

    crear_indices(col)

    # ─ Resumen final ──────────────────────────────────────────────────────────
    print("\n📊 Resumen por tipo de log:")
    for tipo in TIPO_CONFIG:
        conteo = col.count_documents({"tipo": tipo})
        print(f"   {tipo:<15} {conteo:>5} documentos")

    print(f"\n✅ Seeding completado: {total} documentos insertados en '{DB_NAME}.{COL_NAME}'")
    print("═" * 60)
    client.close()

if __name__ == "__main__":
    main()