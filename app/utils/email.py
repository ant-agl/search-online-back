import logging
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSender:
    def __init__(self, receiver_email: str, verification_code: str):
        self.receiver_email = receiver_email
        self.verification_code = verification_code
        self.attempts = 0
        self.logger = logging.getLogger(self.__class__.__name__)

    async def __send_email(self, msg, username, password):
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(username, password)
            self.logger.info("Logged in")
            server.send_message(msg)
            self.logger.info("Sent")
            server.quit()
            return
        except smtplib.SMTPException as e:
            self.logger.warning(f"Failed to send email <{e}>")
            self.attempts += 1
            time.sleep(5)
            if self.attempts < 5:
                await self.__send_email(msg, username, password)
            else:
                raise Exception(f"Failed to send email <{e}>")

    async def send_repair_email(self):
        smtp_user = ""
        smtp_pass = ""
        with open(
            "/static/emails/repair_pwd.html", "r", encoding="utf-8",
        ) as f:
            content = f.read()

        content = content.replace("replace", self.verification_code)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Код подтверждения смены пароля"
        msg["From"] = smtp_user
        msg["To"] = self.receiver_email

        msg.attach(MIMEText(content, "html"))

        await self.__send_email(msg, smtp_user, smtp_pass)

