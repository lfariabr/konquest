import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_nps_failure_notification(sender_email, sender_password):
    # Lista de destinatários
    recipients = [
        # "marcia@procorpoestetica.com.br",
        # "patricia.coutinho@procorpoestetica.com.br",
        # "eliane.climaco@procorpoestetica.com.br",
        # "coc@procorpoestetica.com.br",
        "luis.faria@procorpoestetica.com.br"
    ]

    # Assunto e corpo do email
    subject = "[Pró-Corpo] Automação NPS falhou"
    body = """Olá,

O disparo do NPS falhou para os seguintes números:
- SOROCABA

Vocês poderiam conferir, por favor? Link da planilha:
https://docs.google.com/spreadsheets/d/1c8vA0uQYuGbkSPwlRQnRKeR_zFDmoasoFQCURQ9aSvg/

Obrigado!
"""

    # Criar a mensagem de email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Enviar o email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())
            print("Email enviado com sucesso para os destinatários!")
    except Exception as e:
        print(f"Falha ao enviar o email: {e}")

# Send the invite
sender_email = "rpdprocorpo@gmail.com"
sender_password = "mzqs vdks erxm jaht"  # Use an app-specific password if needed

send_nps_failure_notification(sender_email, sender_password)