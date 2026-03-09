import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Prueba de correo")
msg["Subject"] = "Test"
msg["From"] = "jpcanonr@gmail.com"
msg["To"] = "jpcanonr@gmail.com"

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login("jpcanonr@gmail.com", "hadujswbcsunmamd")
    server.send_message(msg)

print("Correo enviado")
