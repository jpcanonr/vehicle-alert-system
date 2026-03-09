from fastapi import FastAPI
from pydantic import BaseModel
import pika, os, json, logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [API] [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/logs/api.log")
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

# Pool de conexiones (singleton) con protección de concurrencia
import threading

class RabbitMQPool:
    # Se mantiene un `threading.local` para que cada hilo tenga su propia conexión y canal.
    _local = threading.local()
    _lock = threading.Lock()

    @classmethod
    def get_channel(cls):
        # Cada hilo consulta su propia conexión almacenada en thread-local
        conn = getattr(cls._local, "connection", None)
        chan = getattr(cls._local, "channel", None)

        if conn is None or getattr(conn, "is_closed", True):
            # proteger la creación para evitar que varios hilos abran conexiones simultáneas
            with cls._lock:
                conn = getattr(cls._local, "connection", None)
                if conn is None or getattr(conn, "is_closed", True):
                    try:
                        conn = pika.BlockingConnection(
                            pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST", "rabbitmq"))
                        )
                        chan = conn.channel()
                        chan.queue_declare(queue="events")
                        cls._local.connection = conn
                        cls._local.channel = chan
                        logger.info("Conexión RabbitMQ inicializada (thread=%s)", threading.get_ident())
                    except Exception as e:
                        # limpiar para que el siguiente intento recree
                        cls._local.connection = None
                        cls._local.channel = None
                        logger.error(f"Error inicializando conexión RabbitMQ: {e}")
                        raise
        return chan

# Tipo de datos de las coordenadas
class Coordinates(BaseModel):
    latitude: float
    longitude: float

# Tipo de datos de los eventos
class Event(BaseModel):
    type: str
    vehicle_plate: str
    coordinates: Coordinates
    status: str

@app.post("/events")
def receive_event(event: Event):
    body = event.model_dump()
    body["received_at"] = datetime.utcnow().isoformat()
    try:
        channel = RabbitMQPool.get_channel()
        channel.basic_publish(
            exchange="",
            routing_key="events",
            body=json.dumps(body).encode("utf-8")
        )
        logger.info(f"Evento recibido y publicado: {event.type} - Placa {event.vehicle_plate}")
        return {"status": "ok"}
    except Exception as e:
        # en caso de fallo forzamos recreación de la conexión la próxima vez
        thread_local = RabbitMQPool._local
        thread_local.connection = None
        thread_local.channel = None
        logger.error(f"Error publicando evento (se limpiará conexión): {e}")
        return {"status": "error"}
