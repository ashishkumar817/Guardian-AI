from fastapi_mail import FastMail, MessageSchema, MessageType
from app.core.mail import conf


async def send_otp_email(email: str, otp: str):

    html = f"""
    <html>
        <body style="font-family:Arial;">
            <h2>GuardianAI Password Reset</h2>

            <p>Your OTP is:</p>

            <h1 style="color:#2563eb;">{otp}</h1>

            <p>This OTP is valid for <b>5 minutes</b>.</p>

            <p>If you didn't request this, please ignore this email.</p>

            <br>

            <p>GuardianAI Team</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="GuardianAI Password Reset OTP",
        recipients=[email],
        body=html,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)

    await fm.send_message(message)