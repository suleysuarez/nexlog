# NexLog — Sistema de observabilidad para Fintech

Sistema de logging y observabilidad para **Nequi** (Bancolombia). Registra 6 tipos de eventos del ciclo de vida de una operación financiera: `AUTH`, `TRANSACTION`, `SECURITY`, `ERROR`, `AUDIT`, `ACCESS`. Construido con FastAPI + Motor async + MongoDB, contenerizado con Docker y con pipeline CI/CD automatizado en GitHub Actions.

---

## Arquitectura

### Diagrama 1 — Componentes del sistema

```
┌─────────────┐   HTTP REST    ┌──────────────────────────────────┐   Motor async   ┌─────────────────────┐
│   Cliente   │ ─────────────► │         FastAPI (nexlog-api)     │ ───────────────► │      MongoDB        │
│  Postman /  │                │  ┌────────────┐  ┌────────────┐  │                  │   fintech_logs      │
│    App      │                │  │  Pydantic  │  │Motor async │  │                  │  ┌───────────────┐  │
└─────────────┘                │  │ Validación │  │   Driver   │  │                  │  │ colección logs│  │
                               │  └────────────┘  └────────────┘  │                  │  └───────────────┘  │
                               └──────────────────────────────────┘                  │  ┌───────────────┐  │
                                                                                      │  │    Índices    │  │
                                                                                      │  │ timestamp,TTL │  │
                                                                                      │  └───────────────┘  │
                                                                                      └─────────────────────┘
```

### Diagrama 2 — Despliegue Docker

```
┌──────────────────────────────────────────────────────────────────────┐
│  HOST (máquina local o servidor)                                     │
│                                                                      │
│  ┌──────────────────────────┐    ┌──────────────────────────────┐   │
│  │   nexlog-api             │    │   nexlog-mongodb             │   │
│  │   Contenedor API         │    │   Contenedor MongoDB         │   │
│  │                          │    │                              │   │
│  │  Imagen: python:3.12-slim│    │  Imagen: mongo:7.0           │   │
│  │  Puerto: 8000:8000       │    │  Puerto: 27017:27017         │   │
│  │  healthcheck: /health    │    │  healthcheck: mongosh ping   │   │
│  └────────────┬─────────────┘    └──────────────────────────────┘   │
│               │         Motor async (red interna)         │          │
│               └──────────────────────────────────────────►│          │
│                                                            │          │
│               Red interna Docker — nexlog-network          │          │
│                                                  ┌─────────┴───────┐ │
│                                                  │  mongodb_data   │ │
│                                                  │  Volumen        │ │
│                                                  │  persistente    │ │
│                                                  └─────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
         ▲
         │ localhost:8000
  Navegador / Postman
```

### Diagrama 3 — Flujo de alto nivel

```
Usuario Nequi
     │  Hace una transferencia
     ▼
  App Nequi
     │  HTTP POST /logs
     ▼
API NexLog (FastAPI)
  ├── Valida con Pydantic
  └── Calcula expires_at automáticamente
     │  Motor async
     ▼
  MongoDB — colección: logs
     │
     ├── AUTH        (retención: 1 año)
     ├── TRANSACTION (retención: 3 años)
     ├── SECURITY    (retención: 90 días)
     ├── ERROR       (retención: 90 días)
     ├── AUDIT       (retención: 5 años — obligatorio SFC 029/2014)
     └── ACCESS      (retención: 30 días)
          │
          ▼
     TTL automático — MongoDB elimina según expires_at

correlation_id une AUTH + TRANSACTION + AUDIT del mismo flujo
```

---

## Stack tecnológico

| Componente       | Tecnología             | Versión   |
|------------------|------------------------|-----------|
| API              | FastAPI                | 0.111.0   |
| Driver MongoDB   | Motor (async)          | 3.4.0     |
| Validación       | Pydantic               | 2.7.0     |
| Servidor         | Uvicorn                | 0.29.0    |
| Base de datos    | MongoDB                | 7.0       |
| Contenedores     | Docker + Compose       | latest    |
| CI/CD            | GitHub Actions         | —         |
| Tests unitarios  | pytest + httpx         | —         |
| Tests de carga   | k6                     | latest    |

---

## Instalación rápida

```bash
# 1. Clonar el repositorio
git clone https://github.com/suleysuarez/nexlog.git
cd nexlog

# 2. Cambiarse a develop
git checkout develop
git pull origin develop

# 3. Crear tu rama de trabajo
git checkout -b feature/lo-que-hagas

# 4. Levantar todo el sistema
docker compose up -d

# 5. Verificar que funciona
curl http://localhost:8000/health

# 6. Poblar con datos de prueba
docker compose exec api python scripts/seed.py
```

La documentación interactiva de la API estará disponible en: **http://localhost:8000/docs**

---

## Endpoints de la API

| Método | Ruta                              | Descripción                          | Status codes     |
|--------|-----------------------------------|--------------------------------------|------------------|
| GET    | `/health`                         | Estado del servicio                  | 200              |
| POST   | `/api/v1/logs`                    | Crear un nuevo log                   | 201, 422         |
| GET    | `/api/v1/logs`                    | Listar logs con filtros y paginación | 200              |
| GET    | `/api/v1/logs/{id}`               | Detalle de un log por su `_id`       | 200, 400, 404    |
| PUT    | `/api/v1/logs/{id}`               | Actualizar `severity` o `detail`     | 200, 400, 404    |
| DELETE | `/api/v1/logs/{id}`               | Eliminar un log                      | 204, 400, 404    |
| GET    | `/api/v1/logs/traza/{corr_id}`    | Trazabilidad completa por operación  | 200, 404         |

---

## Filtros disponibles en GET /logs

Todos los filtros son opcionales y combinables:

```
GET /api/v1/logs?type=ERROR&service=pagos-service&severity=CRITICAL
GET /api/v1/logs?from_date=2025-01-01&to_date=2025-12-31
GET /api/v1/logs?user_id=usr_col_3829104
GET /api/v1/logs?correlation_id=corr_nequi_8f3a&limit=50&skip=0
```

| Parámetro        | Tipo     | Descripción                                                        |
|------------------|----------|--------------------------------------------------------------------|
| `type`           | string   | Tipo de log: AUTH, TRANSACTION, SECURITY, ERROR, AUDIT, ACCESS     |
| `service`        | string   | Microservicio que generó el evento                                 |
| `severity`       | string   | Nivel: DEBUG, INFO, WARNING, ERROR, CRITICAL                       |
| `from_date`      | datetime | Filtro de fecha inicio                                             |
| `to_date`        | datetime | Filtro de fecha fin                                                |
| `user_id`        | string   | Usuario o microservicio que generó el evento                       |
| `correlation_id` | string   | Agrupa todos los logs de una misma operación                       |
| `limit`          | int      | Documentos por página (máx. 100, default: 20)                      |
| `skip`           | int      | Desplazamiento para paginación (default: 0)                        |

---

## Tipos de log

| Tipo        | Descripción                                                   | Retención |
|-------------|---------------------------------------------------------------|-----------|
| AUTH        | Autenticación — cada acceso a la app Nequi                    | 1 año     |
| TRANSACTION | Pagos, transferencias y depósitos (P2P, P2B, RECHARGE)        | 3 años    |
| SECURITY    | Alertas del motor antifraude                                  | 90 días   |
| ERROR       | Fallos técnicos del sistema                                   | 90 días   |
| AUDIT       | Cambios en datos del usuario — **obligatorio SFC 029/2014**   | 5 años    |
| ACCESS      | Registro HTTP de cada llamada a la API                        | 30 días   |

---

## Tests

```bash
# Tests unitarios (sin MongoDB — usan mocks)
pytest tests/unit/ -v

# Tests unitarios con reporte de cobertura
pytest tests/unit/ -v --cov=app --cov-report=term-missing

# Tests de integración (requiere MongoDB corriendo)
pytest tests/integration/ -v

# Todos los tests
pytest tests/ -v

# Tests de carga (requiere sistema completo + seed)
./run_load_test.sh
```

---

## Estructura del proyecto

```
nexlog/
├── app/
│   ├── main.py          ← punto de entrada FastAPI
│   ├── database.py      ← conexión Motor async + índices
│   ├── models.py        ← modelos Pydantic + política de retención
│   └── routes/
│       └── logs.py      ← todos los endpoints CRUD + trazabilidad
├── scripts/
│   └── seed.py          ← datos de prueba (Persona 1)
├── tests/
│   ├── conftest.py      ← fixtures compartidos
│   ├── unit/            ← tests con mocks (sin MongoDB)
│   │   ├── test_health.py
│   │   ├── test_health_extended.py
│   │   ├── test_post_logs.py
│   │   ├── test_get_logs.py
│   │   └── test_put_delete_logs.py
│   └── integration/     ← tests con MongoDB real (fintech_logs_test)
│       ├── conftest.py
│       └── test_connection.py
├── k6/
│   └── k6_script.js     ← tests de carga con escenarios mixtos
├── .github/
│   └── workflows/
│       └── ci.yml       ← pipeline CI/CD automático
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Variables de entorno

Crear un archivo `.env` en la raíz del proyecto (no subir a GitHub):

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=fintech_logs
API_PORT=8000
```

---

## Comandos Docker útiles

```bash
# Levantar todo en segundo plano
docker compose up -d

# Ver estado de los contenedores
docker compose ps

# Ver logs de la API en tiempo real
docker compose logs -f api

# Ver logs de MongoDB
docker compose logs -f mongodb

# Detener todo
docker compose down

# Detener y eliminar volumen de datos (borra todos los datos)
docker compose down -v

# Reconstruir imagen y levantar
docker compose up -d --build
```

---

## Decisiones técnicas

**Motor async sobre PyMongo** — El modelo de negocio Fintech de alto volumen (hasta 500.000 eventos/hora) requiere un driver asíncrono. Motor se integra nativamente con FastAPI sin bloquear el event loop.

**Colección única con `expires_at`** — En lugar de 6 colecciones separadas (una por tipo de log), NexLog usa una sola colección con TTL Index diferenciado por documento. Esto simplifica las consultas de trazabilidad: un solo `find` con `correlation_id` devuelve todos los eventos de una operación sin JOINs.

**AUDIT retiene 5 años** — La Circular SFC 029/2014 de la Superfinanciera obliga a las Fintech colombianas a mantener registros de cambios en datos sensibles por mínimo 5 años. No es negociable.

**IPs anonimizadas** — La Ley 1581 de 2012 (Habeas Data Colombia) exige que los datos personales como direcciones IP se anonimicen. Se muestran solo los primeros tres octetos.

**Índice compuesto `(type, timestamp)`** — El patrón de consulta más frecuente es filtrar por tipo y ordenar por fecha. El índice compuesto cubre ambas operaciones en una sola pasada sobre el árbol B.

**`GET /traza` declarado antes que `GET /{id}`** — FastAPI resuelve rutas por orden de declaración. Si `/{id}` se declara primero, FastAPI interpreta la palabra `traza` como un ObjectId y devuelve 400.

---

## Microservicios de Nequi

| Microservicio           | Función                                        | Tipos de log generados |
|-------------------------|------------------------------------------------|------------------------|
| auth-service            | Autenticación, biometría, tokens JWT           | AUTH, ACCESS           |
| pagos-service           | Transferencias P2P                             | TRANSACTION, ERROR     |
| recarga-service         | Depósitos de efectivo (Efecty, Baloto)         | TRANSACTION, ERROR     |
| antifraude-service      | Motor de detección de fraude                   | SECURITY               |
| auditoria-service       | Cambios en datos sensibles del usuario         | AUDIT                  |
| gateway-service         | API Gateway — enruta todas las peticiones HTTP | ACCESS                 |
| notificaciones-service  | Push, SMS y notificaciones                     | ERROR, ACCESS          |
| pse-service             | Pagos QR en establecimientos (P2B)             | TRANSACTION, ERROR     |

---

## Equipo

| Persona   | Nombre            | Rol                   | Responsabilidades                              |
|-----------|-------------------|-----------------------|------------------------------------------------|
| Persona 1 | Jherson Sanchez   | Arquitecto de datos   | MongoDB, esquemas, seed.py                     |
| Persona 2 | Sebastian Valero  | Desarrollador de API  | FastAPI, Motor async, Pydantic, endpoints CRUD |
| Persona 3 | Suley Suarez      | DevOps                | Docker, GitHub Actions, tests de carga k6      |
| Persona 4 | Jhonatan Vera     | QA y documentación    | pytest, diagramas, README                      |

---

## Regulación aplicable

- **Circular SFC 029/2014** — Superfinanciera: retención mínima de 5 años para registros AUDIT
- **Ley 1581 de 2012** — Habeas Data Colombia: anonimización de IPs y datos personales

---

*Universidad de Pamplona — Bases de Datos NoSQL 2025-2*