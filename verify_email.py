import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Prueba de correo")
msg["Subject"] = "Test"
msg["From"] = "juanpcr2009@gmail.com"
msg["To"] = "juanpcr2009@gmail.com"

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login("juanpcr2009@gmail.com", "opgrhevnwwktzywv")
    server.send_message(msg)

print("Correo enviado")
