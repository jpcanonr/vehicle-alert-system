import http from 'k6/http';
import { check } from 'k6';

const configuredRate = 20;

export const options = {
    scenarios: {
        configurable_rate_test: {
            executor: 'constant-arrival-rate',
            rate: configuredRate,      // valor configurable
            timeUnit: '1s',
            duration: '30s',
            preAllocatedVUs: 50,
            maxVUs: 200,
        },
    },
    thresholds: {
        // opcional: marcar como fallo si alguna solicitud devuelve 429 (tasa mayor que 0)
        'http_req_failed{status:429}': ['rate>0'],
    },
};

export default function () {
  const url = 'http://localhost:8080/events';
  const payload = JSON.stringify({
    type: Math.random() < 0.01 ? 'Emergency' : 'Position',
    vehicle_plate: 'ABC-123',
    coordinates: { latitude: 12.345, longitude: 67.89 },
    status: 'OK',
  });

  const params = { headers: { 'Content-Type': 'application/json' } };

  const res = http.post(url, payload, params);
  check(res, { 'status is 200': (r) => r.status === 200 });
}
