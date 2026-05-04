// k6/k6_script.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');
const BASE = __ENV.BASE_URL || 'http://localhost:8000/api/v1';
const TIPOS = ['AUTH', 'TRANSACTION', 'SECURITY', 'ERROR', 'AUDIT', 'ACCESS'];
const DURATION = __ENV.K6_DURATION || '3m30s';

export const options = {
  scenarios: {
    listar_por_tipo: {
      executor: 'constant-vus',
      exec: 'escenarioListarPorTipo',
      vus: 50,
      duration: DURATION,
    },
    listar_por_fecha: {
      executor: 'constant-vus',
      exec: 'escenarioListarPorFecha',
      vus: 25,
      duration: DURATION,
    },
    crear_log: {
      executor: 'constant-vus',
      exec: 'escenarioCrearLog',
      vus: 25,
      duration: DURATION,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<300'],
    http_req_failed:   ['rate<0.01'],
    errors:            ['rate<0.05'],
  },
};

export function escenarioListarPorTipo() {
  const tipo = TIPOS[Math.floor(Math.random() * TIPOS.length)];
  const res = http.get(`${BASE}/logs?type=${tipo}&limit=20`);
  const ok = check(res, {
    'GET /logs status 200':    (r) => r.status === 200,
    'tiene resultados reales': (r) => JSON.parse(r.body).total > 0,
  });
  errorRate.add(!ok);
  sleep(0.5 + Math.random());
}

export function escenarioListarPorFecha() {
  const res = http.get(`${BASE}/logs?from_date=2025-01-01&to_date=2025-12-31&limit=20`);
  const ok = check(res, {
    'GET /logs fecha status 200': (r) => r.status === 200,
  });
  errorRate.add(!ok);
  sleep(0.5 + Math.random());
}

export function escenarioCrearLog() {
  const payload = JSON.stringify({
    type:           TIPOS[Math.floor(Math.random() * TIPOS.length)],
    severity:       'INFO',
    service:        'gateway-service',
    correlation_id: `corr_k6_${Date.now()}`,
    user_id:        `usr_k6_${Math.floor(Math.random() * 10000)}`,
    detail: {
      fuente:       'k6-load-test',
      timestamp_k6: Date.now(),
    },
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