import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def _build_smtp_connection() -> smtplib.SMTP:
    """Create and return an authenticated SMTP connection."""
    smtp = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
    if settings.SMTP_USE_TLS:
        smtp.starttls()
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
    return smtp


def send_verification_email(to_email: str, code: str, first_name: str) -> None:
    """Send a 6-digit verification code to the user's email after registration."""
    subject = "Clinix — Verify Your Email"
    html_body = f"""\
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>Welcome to Clinix, {first_name}!</h2>
        <p>Use the code below to verify your email address:</p>
        <div style="
            font-size: 32px;
            font-weight: bold;
            letter-spacing: 6px;
            background: #f4f4f4;
            padding: 16px 24px;
            border-radius: 8px;
            display: inline-block;
            margin: 16px 0;
        ">{code}</div>
        <p>This code expires in <strong>{settings.EMAIL_VERIFY_EXPIRE_MINUTES} minutes</strong>.</p>
        <p>If you didn't create an account, you can safely ignore this email.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(f"Your Clinix verification code is: {code}", "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with _build_smtp_connection() as smtp:
        smtp.sendmail(settings.EMAIL_FROM_EMAIL, to_email, msg.as_string())
