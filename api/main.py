from fastapi import FastAPI
from pydantic import BaseModel
import pika, os, json, logging, time
from datetime import datetime
import threading # Pool de conexiones (singleton) con protección de concurrencia

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
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "secret")

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
            with cls._lock:
                conn = getattr(cls._local, "connection", None)
                if conn is None or getattr(conn, "is_closed", True):
                    for attempt in range(5):
                        try:
                            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
                            conn = pika.BlockingConnection(
                                pika.ConnectionParameters(
                                    host=RABBITMQ_HOST,
                                    credentials=credentials,
                                    heartbeat=30,
                                    blocked_connection_timeout=30
                                )
                            )
                            chan = conn.channel()
                            chan.queue_declare(queue="events", durable=True) # durable=True para asegurar que la cola sobreviva a reinicios
                            cls._local.connection = conn
                            cls._local.channel = chan
                            logger.info("Conexión RabbitMQ inicializada (thread=%s)", threading.get_ident())
                            break
                        except Exception as e:
                            logger.error(f"Error inicializando conexión RabbitMQ: {e}, intento {attempt+1}")
                            time.sleep(2 ** attempt)
                            cls._local.connection = None
                            cls._local.channel = None
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
            body=json.dumps(body).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2)  # delivery_mode=2 MEnsajes persistentes para asegurar que no se pierdan si RabbitMQ se reinicia
        )
        logger.info(f"Evento recibido y publicado: {event.type} - Placa {event.vehicle_plate}")
        return {"status": "ok"}
    except Exception as e:
        RabbitMQPool._local.connection = None
        RabbitMQPool._local.channel = None
        logger.error(f"Error publicando evento: {e}")
        return {"status": "error"}
