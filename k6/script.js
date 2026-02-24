import http from 'k6/http';
import { check } from 'k6';

export const options = {
  // vus: 10,
  // iterations: 1000,
  
  // Usamos un scenario de tipo `constant-arrival-rate` para generar
  // ~1000 peticiones en 30 segundos.
  // rate = ceil(1000 / 30) = 34 req/s → 34 * 30 = 1020 peticiones (aprox. 1000)
  scenarios: {
    constant_rate: {
      executor: 'constant-arrival-rate',
      rate: 34,
      timeUnit: '1s', // 34 iterations por segundo
      duration: '30s',
      preAllocatedVUs: 50, // VUs prealocados para mantener la tasa
      maxVUs: 200,
    },
  },
};

export default function () {
  const url = 'http://localhost:8080/events';
  const payload = JSON.stringify({
    type: Math.random() < 0.1 ? 'Emergency' : 'Position',
    vehicle_plate: 'ABC-123',
    coordinates: { latitude: 12.345, longitude: 67.89 },
    status: 'OK',
  });

  const params = { headers: { 'Content-Type': 'application/json' } };

  const res = http.post(url, payload, params);
  check(res, { 'status is 200': (r) => r.status === 200 });
}
