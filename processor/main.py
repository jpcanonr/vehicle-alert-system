import pika, os, json, time, requests, logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PROCESSOR] [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/logs/processor.log")
    ]
)
logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
NOTIFIER_URL = os.getenv("NOTIFIER_URL", "http://notifier:8001/notify")

# Función para notificar con reintentos exponenciales
def notify(event):
    for attempt in range(3):
        try:
            resp = requests.post(NOTIFIER_URL, json=event)
            if resp.status_code == 200:
                logger.info(f"Correo notificado correctamente en intento {attempt+1}")
                return
            else:
                logger.error(f"Error HTTP {resp.status_code} notificando")
        except Exception as e:
            logger.error(f"Error notificando: {e}, intento {attempt+1}")
        time.sleep(2 ** attempt)

def callback(ch, method, properties, body):
    event = json.loads(body.decode("utf-8"))
    logger.info(f"Evento procesado: {event['type']} - Placa {event['vehicle_plate']}")
    if event.get("type") == "Emergency":
        logger.info(f"Detectado Emergency: {event}")
        notify(event)

def main():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            channel = connection.channel()
            channel.queue_declare(queue="events")
            channel.basic_consume(queue="events", on_message_callback=callback, auto_ack=True)
            logger.info("Processor esperando mensajes...")
            channel.start_consuming()
        except Exception as e:
            logger.error(f"Error en Processor: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
