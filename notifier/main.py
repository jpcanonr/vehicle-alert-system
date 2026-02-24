from fastapi import FastAPI
from pydantic import BaseModel
import os, smtplib, logging
from email.mime.text import MIMEText

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [NOTIFIER] [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/logs/notifier.log")
    ]
)
logger = logging.getLogger(__name__)

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
TO_EMAIL = GMAIL_USER  # se envía a tu propio correo

app = FastAPI()

class Event(BaseModel):
    type: str
    vehicle_plate: str
    status: str

def send_email(event: Event):
    # Asunto con emojis
    subject = "🚨 Alerta de Emergencia 🚨"

    # Cuerpo del mensaje con formato más claro
    body = f"""
🚨 Alerta de Emergencia 🚨

Placa: {event.vehicle_plate}
Estado: {event.status}
Evento: {event.type}
"""

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        logger.info(f"Correo enviado exitosamente a {TO_EMAIL}")
    except Exception as e:
        logger.error(f"Error enviando correo: {e}")

@app.post("/notify")
def notify(event: Event):
    logger.info(f"Solicitud de notificación recibida: {event}")
    send_email(event)
    return {"status": "email_sent"}
