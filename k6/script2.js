import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 10,          // número de usuarios virtuales
  iterations: 1000, // total de peticiones
};

export default function () {
  // Genera una placa única de 000 a 999
  const plate = `CAR-${__ITER.toString().padStart(3, '0')}`;

  const payload = JSON.stringify({
    type: Math.random() < 0.1 ? 'Emergency' : 'Position',
    vehicle_plate: plate,
    coordinates: { latitude: 12.345, longitude: 67.890 },
    status: "OK"
  });

  const headers = { "Content-Type": "application/json" };

  const res = http.post("http://localhost:8080/events", payload, { headers });

  check(res, {
    "status is 200": (r) => r.status === 200,
  });
}
