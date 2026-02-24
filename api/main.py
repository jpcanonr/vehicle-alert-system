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

# Pool de conexiones (singleton)
class RabbitMQPool:
    connection = None
    channel = None

    @classmethod
    def get_channel(cls):
        if cls.connection is None or cls.connection.is_closed:
            try:
                cls.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=RABBITMQ_HOST)
                )
                cls.channel = cls.connection.channel()
                cls.channel.queue_declare(queue="events")
                logger.info("Conexión RabbitMQ inicializada")
            except Exception as e:
                logger.error(f"Error inicializando conexión RabbitMQ: {e}")
                raise
        return cls.channel

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
        logger.error(f"Error publicando evento: {e}")
        return {"status": "error"}
