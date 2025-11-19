import pika, os, time, json, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
QUEUE_NAME = os.getenv("RABBIT_QUEUE", "notifications")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")


def send_email(to_email, subject, html_body):
    """Envía email SMTP usando Gmail"""
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, to_email, msg.as_string())


def process_notification(body):
    data = json.loads(body)

    if data["type"] == "appointment_reserved":
        paciente_email = data["email"]

        if not paciente_email:
            print("No email found for paciente. Skipping.")
            return

        subject = "Confirmación de reserva - MedSUY"
        html = f"""
        <h2>Tu turno fue reservado correctamente</h2>
        <p><strong>Especialidad:</strong> {data['specialty']}</p>
        <p><strong>Médico:</strong> {data['doctor']}</p>
        <p><strong>Fecha y hora:</strong> {data['datetime']}</p>
        <p><strong>Sucursal:</strong> {data['branch']}</p>

        <br>
        <p>Gracias por usar MedSUY ❤️</p>
        """

        print(f"Enviando email a {paciente_email}...")
        send_email(paciente_email, subject, html)
        print("Email enviado correctamente.")


def main():
    while True:
        try:
            print("Conectando a RabbitMQ...")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST)
            )
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            print("Worker escuchando la cola:", QUEUE_NAME)

            def callback(ch, method, properties, body):
                print("Mensaje recibido:", body.decode())
                process_notification(body.decode())
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=callback
            )

            channel.start_consuming()

        except Exception as e:
            print("Error en worker:", e)
            time.sleep(3)


if __name__ == "__main__":
    main()
