import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from dotenv import load_dotenv
from main_logging import logging_func,logging
# Load environment variables
load_dotenv(interpolate=True, override=True)


class MailSender:
    
    def __init__(self, **kwargs):
        self.email = kwargs.get("email") or os.getenv("email")
        self.password = kwargs.get("password") or os.getenv("password")
        self.smtp_server = kwargs.get("smtp_server") or os.getenv("smtp_server")
        self.port = kwargs.get("port") or os.getenv("port")
        
        self.get_email_config()
        
    def get_email_config(self):
        try:

            if not self.email:
                raise ValueError("❌ email is missing in .env or as param in class")
            if not self.password:
                raise ValueError("❌ password is missing in .env or as param in class")
            if not self.smtp_server:
                raise ValueError("❌ smtp_server is missing in .env or as param in class")
            if not self.port:
                raise ValueError("❌ port is missing in .env or as param in class")

            return self.email, self.password, self.smtp_server, int(self.port)

        except Exception as e:
            print(f"⚠️ Error loading config: {e}")
            exit()
    @logging_func
    def send_mail(self,recipient_email, subject, body):
        email, password, smtp_server, port = self.get_email_config()

        # Create a MIME multipart message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = email
        message["To"] = recipient_email
        message["Date"] = formatdate(localtime=True)

        # Add HTML body
        html_part = MIMEText(body, "html")
        message.attach(html_part)

        try:
            with smtplib.SMTP(smtp_server, port) as server:
                server.starttls()
                server.login(email, password)
                server.sendmail(email, recipient_email, message.as_string())
            logging.info("email send sucess")
            print("✅ Email sent successfully!")
        except Exception as e:
            print(f"❌ Error sending email: {e}")
