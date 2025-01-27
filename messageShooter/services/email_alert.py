import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import logging
logger = logging.getLogger(__name__)

def end_of_queue_email():
    # Lista de destinatários
    recipients = [
        "luis.faria@18digital.com.br"
    ]

    # Assunto e corpo do email
    subject = "[konquista] Queue processing finished"
    body = f"""Hello, the queue processor has been finished.
    """

    # Criar a mensagem de email
    msg = MIMEMultipart()
    msg['From'] = "rpdprocorpo@gmail.com"
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Enviar o email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login("rpdprocorpo@gmail.com", "mzqs vdks erxm jaht")
            server.sendmail("rpdprocorpo@gmail.com", recipients, msg.as_string())
            logger.info("Email enviado com sucesso para os destinatários!")
    except Exception as e:
        logger.info(f"Falha ao enviar o email: {e}")

def send_nps_failure_notification(message):
    # Lista de destinatários
    recipients = [
        "marcia@procorpoestetica.com.br",
        "patricia.coutinho@procorpoestetica.com.br",
        "eliane.climaco@procorpoestetica.com.br",
        "coc@procorpoestetica.com.br",
        "luis.faria@18digital.com.br"
    ]

    # Assunto e corpo do email
    subject = "[konquista] Alerta - Tokens Inválidos ⚠️"
    body = f"""Olá,

    {message}

    Vocês poderiam conferir, por favor? Link da planilha:
    https://docs.google.com/spreadsheets/d/1c8vA0uQYuGbkSPwlRQnRKeR_zFDmoasoFQCURQ9aSvg/

    Obrigado!
    """

    # Criar a mensagem de email
    msg = MIMEMultipart()
    msg['From'] = "rpdprocorpo@gmail.com"
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Enviar o email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login("rpdprocorpo@gmail.com", "mzqs vdks erxm jaht")
            server.sendmail("rpdprocorpo@gmail.com", recipients, msg.as_string())
            logger.info("Email enviado com sucesso para os destinatários!")
    except Exception as e:
        logger.info(f"Falha ao enviar o email: {e}")

# Test code - only runs when script is executed directly
if __name__ == "__main__":
    test_message = "Test notification message."
    send_nps_failure_notification(test_message)