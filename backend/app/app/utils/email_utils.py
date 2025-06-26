from email.message import EmailMessage
import aiosmtplib
import os
from dotenv import load_dotenv

load_dotenv()


async def send_email_async (to_email : str , subject : str , body: str) :
    message = EmailMessage()
    message["From"] =  os.getenv("EMAIL_FROM")
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    
    await aiosmtplib.send(
        message,
        hostname=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT")),
        username=os.getenv("SMTP_USER"),
        password=os.getenv("SMTP_PASS"),
        use_tls=True)