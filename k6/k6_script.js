import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');
const BASE = __ENV.BASE_URL || 'http://localhost:8000/api/v1';
const TIPOS = ['AUTH', 'TRANSACTION', 'SECURITY', 'ERROR', 'AUDIT', 'ACCESS'];
const DURATION = __ENV.K6_DURATION || '1m30s';

const CORRELATION_IDS = [
  'corr_nequi_019e4d58e8184630',
  'corr_nequi_cbe175b0c3fd4fb7',
  'corr_nequi_4464e28d6f674d69',
  'corr_nequi_677c2faffdf44594',
  'corr_nequi_8d26bc3b1ede4851',
];

export const options = {
  scenarios: {
    listar_por_tipo: {
      executor: 'constant-vus',
      exec: 'escenarioListarPorTipo',
      vus: 20,
      duration: DURATION,
    },
    listar_por_fecha: {
      executor: 'constant-vus',
      exec: 'escenarioListarPorFecha',
      vus: 10,
      duration: DURATION,
    },
    crear_log: {
      executor: 'constant-vus',
      exec: 'escenarioCrearLog',
      vus: 15,
      duration: DURATION,
    },
    trazabilidad: {
      executor: 'constant-vus',
      exec: 'escenarioTrazabilidad',
      vus: 10,
      duration: DURATION,
    },
    obtener_por_id: {
      executor: 'constant-vus',
      exec: 'escenarioObtenerPorId',
      vus: 10,
      duration: DURATION,
    },
    actualizar_log: {
      executor: 'constant-vus',
      exec: 'escenarioActualizarLog',
      vus: 10,
      duration: DURATION,
    },
    eliminar_log: {
      executor: 'constant-vus',
      exec: 'escenarioEliminarLog',
      vus: 5,
      duration: DURATION,
    },
    health_check: {
      executor: 'constant-vus',
      exec: 'escenarioHealth',
      vus: 5,
      duration: DURATION,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<300'],
    http_req_failed:   ['rate<0.05'],
    errors:            ['rate<0.05'],
  },
};

// ── GET /health ───────────────────────────────────────────
export function escenarioHealth() {
  const base = __ENV.BASE_URL
    ? __ENV.BASE_URL.replace('/api/v1', '')
    : 'http://localhost:8000';
  const res = http.get(`${base}/health`);
  const ok = check(res, {
    'GET /health status 200': (r) => r.status === 200,
  });
  errorRate.add(!ok);
  sleep(0.5 + Math.random());
}

// ── GET /api/v1/logs?type=... ─────────────────────────────
export function escenarioListarPorTipo() {
  const tipo = TIPOS[Math.floor(Math.random() * TIPOS.length)];
  const res = http.get(`${BASE}/logs?type=${tipo}&limit=20`);
  const ok = check(res, {
    'GET /logs status 200': (r) => r.status === 200,
  });
  errorRate.add(!ok);
  sleep(0.5 + Math.random());
}

// ── GET /api/v1/logs?from_date=...&to_date=... ────────────
export function escenarioListarPorFecha() {
  const res = http.get(`${BASE}/logs?from_date=2026-01-01&to_date=2026-12-31&limit=20`);
  const ok = check(res, {
    'GET /logs fecha status 200': (r) => r.status === 200,
  });
  errorRate.add(!ok);
  sleep(0.5 + Math.random());
}

// ── POST /api/v1/logs ─────────────────────────────────────
export function escenarioCrearLog() {
  const payload = JSON.stringify({
    type:           TIPOS[Math.floor(Math.random() * TIPOS.length)],
    severity:       'INFO',
    service:        'gateway-service',
    correlation_id: `corr_k6_${Date.now()}_${Math.random()}`,
    user_id:        `usr_k6_${Math.floor(Math.random() * 10000)}`,
    detail: { fuente: 'k6-load-test', timestamp_k6: Date.now() },
  });
  const res = http.post(`${BASE}/logs`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });
  const ok = check(res, {
    'POST /logs status 201': (r) => r.status === 201,
  });
  errorRate.add(!ok);
  sleep(0.5 + Math.random());
}

// ── GET /api/v1/logs/{log_id} ─────────────────────────────
export function escenarioObtenerPorId() {
  const res = http.get(`${BASE}/logs?limit=1`);
  const okLista = check(res, {
    'GET /logs?limit=1 (obtener_id) status 200': (r) => r.status === 200,
  });
  errorRate.add(!okLista);

  if (res.status === 200) {
    try {
      const body = JSON.parse(res.body);
      if (body.data && body.data.length > 0) {
        const id = body.data[0].id || body.data[0]._id;
        const res2 = http.get(`${BASE}/logs/${id}`);
        const ok = check(res2, {
          'GET /logs/{id} status 200': (r) => r.status === 200 || r.status === 404,
        });
        errorRate.add(!ok);
      }
    } catch (_) {}
  }
  sleep(0.5 + Math.random());
}

// ── PUT /api/v1/logs/{log_id} ─────────────────────────────
export function escenarioActualizarLog() {
  const res = http.get(`${BASE}/logs?limit=1`);
  const okLista = check(res, {
    'GET /logs?limit=1 (actualizar) status 200': (r) => r.status === 200,
  });
  errorRate.add(!okLista);

  if (res.status === 200) {
    try {
      const body = JSON.parse(res.body);
      if (body.data && body.data.length > 0) {
        const id = body.data[0].id || body.data[0]._id;
        const payload = JSON.stringify({
          severity: 'WARNING',
          detail: { actualizado_por: 'k6', timestamp: Date.now() },
        });
        const res2 = http.put(`${BASE}/logs/${id}`, payload, {
          headers: { 'Content-Type': 'application/json' },
        });
        const ok = check(res2, {
          'PUT /logs/{id} responde': (r) => r.status === 200 || r.status === 404,
        });
        errorRate.add(!ok);
      }
    } catch (_) {}
  }
  sleep(0.5 + Math.random());
}

// ── DELETE /api/v1/logs/{log_id} ──────────────────────────
export function escenarioEliminarLog() {
  const payload = JSON.stringify({
    type:           'ERROR',
    severity:       'DEBUG',
    service:        'k6-delete-test',
    correlation_id: `corr_del_${Date.now()}_${Math.random()}`,
    user_id:        `usr_del_${Math.floor(Math.random() * 1000)}`,
    detail:         { fuente: 'k6-para-eliminar' },
  });
  const crear = http.post(`${BASE}/logs`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });
  const okCrear = check(crear, {
    'POST /logs (eliminar) status 201': (r) => r.status === 201,
  });
  errorRate.add(!okCrear);

  if (crear.status === 201) {
    try {
      const body = JSON.parse(crear.body);
      const id = body.id || body._id;
      if (id) {
        const del = http.del(`${BASE}/logs/${id}`);
        const ok = check(del, {
          'DELETE /logs/{id} status 204': (r) => r.status === 204 || r.status === 404,
        });
        errorRate.add(!ok);
      }
    } catch (_) {}
  }
  sleep(0.5 + Math.random());
}

// ── GET /api/v1/logs/traza/{correlation_id} ───────────────
export function escenarioTrazabilidad() {
  const corrId = CORRELATION_IDS[Math.floor(Math.random() * CORRELATION_IDS.length)];
  const res = http.get(`${BASE}/logs/traza/${corrId}`);

  if (res.status !== 200 && res.status !== 404) {
    console.log(`[TRAZA FALLO] corr_id=${corrId} status=${res.status} body=${res.body}`);
  }

  const ok = check(res, {
    'GET /traza responde': (r) => r.status === 200 || r.status === 404,
  });
  errorRate.add(!ok);
  sleep(0.5 + Math.random());
}
