import asyncio
import os
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from faker import Faker
import random
import uuid

fake = Faker('es_CO')

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "nexlog")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ── Datos del contexto Nequi Colombia ─────────────────────────────────
SERVICIOS = [
    'auth-service', 'pagos-service', 'pse-service',
    'recarga-service', 'antifraude-service',
    'notificaciones-service', 'auditoria-service', 'gateway-service'
]
CIUDADES = [
    'Bogota', 'Medellin', 'Cali', 'Barranquilla', 'Cartagena',
    'Bucaramanga', 'Pereira', 'Manizales', 'Cucuta', 'Ibague'
]
SEVERIDADES = ['DEBUG', 'INFO', 'INFO', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

RETENCION = {
    'ACCESS':      timedelta(days=30),
    'ERROR':       timedelta(days=90),
    'SECURITY':    timedelta(days=90),
    'AUTH':        timedelta(days=365),
    'TRANSACTION': timedelta(days=365*3),
    'AUDIT':       timedelta(days=365*5),
}

# ── Funciones auxiliares ───────────────────────────────────────────────
def nuevo_correlation_id():
    return f'corr_nequi_{uuid.uuid4().hex[:16]}'

def nuevo_usuario_id():
    return f'usr_col_{random.randint(1000000, 9999999)}'

def anonimizar_ip():
    return f'{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.0'

def base_doc(tipo, servicio, usuario_id, correlation_id):
    ts = fake.date_time_between(start_date='-90d', end_date='now')
    return {
        'type':           tipo,
        'severity':       random.choice(SEVERIDADES),
        'timestamp':      ts,
        'service':        servicio,
        'correlation_id': correlation_id,
        'user_id':        usuario_id,
        'expires_at':     ts + RETENCION[tipo],
    }

# ── Generadores por tipo ───────────────────────────────────────────────
def gen_auth(corr, usr):
    doc = base_doc('AUTH', 'auth-service', usr, corr)
    doc['detail'] = {
        'auth_method':     random.choice(['PIN', 'FACIAL_BIOMETRICS', 'VOICE_BIOMETRICS', 'UNBLOCK_REVERIFICATION']),
        'result':          random.choice(['SUCCESS', 'SUCCESS', 'SUCCESS', 'FAILED', 'BLOCKED']),
        'failed_attempts': random.randint(0, 3),
        'device_id':       f'dev_{random.choice(["and","ios"])}_{uuid.uuid4().hex[:6]}',
        'ip_address':      anonimizar_ip(),
        'city':            random.choice(CIUDADES),
        'token_issued':    True,
    }
    return doc

def gen_transaction(corr, usr):
    sub = random.choice(['P2P', 'P2B', 'RECHARGE'])
    doc = base_doc('TRANSACTION', 'pagos-service', usr, corr)
    det = {
        'sub_type':           sub,
        'amount_cop':         random.randint(1000, 5000000),
        'status':             random.choice(['APPROVED', 'APPROVED', 'REJECTED', 'PENDING']),
        'source_account':     None if sub == 'RECHARGE' else f'nequi_****{random.randint(1000,9999)}',
        'processing_time_ms': random.randint(100, 2000),
    }
    if sub == 'P2P':
        det['destination_account'] = f'nequi_****{random.randint(1000,9999)}'
    elif sub == 'P2B':
        det['merchant_id']   = f'merchant_nequi_{random.randint(10000,99999)}'
        det['merchant_name'] = f'Tienda {fake.company()}'
    else:
        det['deposit_point']  = random.choice(['Efecty', 'Baloto', 'Corresponsal_Bancario'])
        det['deposit_city']   = random.choice(CIUDADES)
        det['receipt_number'] = f'REC_2025_{random.randint(10000000,99999999)}'
    doc['detail'] = det
    return doc

def gen_security(corr, usr):
    doc = base_doc('SECURITY', 'antifraude-service', usr, corr)
    doc['detail'] = {
        'alert_type':        random.choice(['UNUSUAL_LOCATION', 'MULTIPLE_FAILED_AUTH', 'SUSPICIOUS_DEPOSIT', 'UNUSUAL_AMOUNT', 'SIMULTANEOUS_SESSION']),
        'risk_level':        random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
        'action_taken':      random.choice(['PREVENTIVE_BLOCK', 'MONITORING', 'REQUIRE_REVERIFICATION']),
        'alert_city':        random.choice(CIUDADES),
        'usual_city':        random.choice(CIUDADES),
        'ip_address':        anonimizar_ip(),
        'resolution_method': random.choice(['PENDING', 'REVERIFIED', 'EXPIRED']),
    }
    return doc

def gen_error(corr, svc):
    doc = base_doc('ERROR', svc, svc, corr)
    doc['detail'] = {
        'error_code':       random.choice(['ERR_TIMEOUT_DB', 'ERR_CONNECTION_REFUSED', 'ERR_NULL_POINTER', 'ERR_INVALID_RESPONSE']),
        'message':          'Error tecnico generado por seed',
        'endpoint':         random.choice(['/api/v1/logs', '/api/v1/transferencias']),
        'http_method':      random.choice(['GET', 'POST', 'PUT', 'DELETE']),
        'response_time_ms': random.randint(1000, 8000),
    }
    return doc

def gen_audit(corr, usr):
    campo = random.choice(['display_name', 'email', 'daily_limit', 'beneficiary_added', 'beneficiary_removed', 'colchon_protection'])
    doc = base_doc('AUDIT', 'auditoria-service', usr, corr)
    doc['detail'] = {
        'modified_field': campo,
        'previous_value': str(random.randint(100000, 500000)) if campo == 'daily_limit' else 'valor_anterior_***',
        'new_value':      str(random.randint(500001, 2000000)) if campo == 'daily_limit' else 'valor_nuevo_***',
        'ip_address':     anonimizar_ip(),
    }
    return doc

def gen_access(corr, svc):
    doc = base_doc('ACCESS', 'gateway-service', svc, corr)
    doc['detail'] = {
        'http_method':      random.choice(['GET', 'POST', 'PUT', 'DELETE']),
        'endpoint':         random.choice(['/api/v1/logs', '/api/v1/logs/traza']),
        'status_code':      random.choice([200, 200, 201, 404, 422, 500]),
        'response_time_ms': random.randint(10, 500),
        'ip_address':       anonimizar_ip(),
        'request_id':       f'req_{uuid.uuid4().hex[:8]}',
    }
    return doc

# ── Main ───────────────────────────────────────────────────────────────
async def main():
    await db['logs'].drop()
    docs = []

    # 50 trazas completas con correlation_id compartido
    print('Generando 50 trazas completas...')
    for _ in range(50):
        corr = nuevo_correlation_id()
        usr  = nuevo_usuario_id()
        docs.append(gen_access(corr, 'gateway-service'))
        docs.append(gen_auth(corr, usr))
        docs.append(gen_transaction(corr, usr))
        docs.append(gen_audit(corr, usr))

    # Completar hasta 1000 documentos
    print('Completando hasta 1000 documentos...')
    generadores = [gen_auth, gen_transaction, gen_security, gen_error, gen_audit, gen_access]
    while len(docs) < 1000:
        corr = nuevo_correlation_id()
        usr  = nuevo_usuario_id()
        gen  = random.choice(generadores)
        try:
            docs.append(gen(corr, usr))
        except TypeError:
            docs.append(gen(corr, 'gateway-service'))

    resultado = await db['logs'].insert_many(docs[:1000])
    print(f'Seed OK: {len(resultado.inserted_ids)} documentos insertados')
    print(f'50 trazas completas con correlation_id para trazabilidad')
    client.close()

asyncio.run(main())