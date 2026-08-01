import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
from datetime import datetime
from app.core.config import settings

def send_fall_alert_email(
    to_email: str,
    recipient_name: str,
    user_name: str,
    incident_time: str,
    confidence: float,
    image_path: str = None
):
    """
    Sends an immediate emergency fall detection email notification to emergency contacts.
    """
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        print("[WARNING] Mail credentials missing in .env, skipping email dispatch.")
        return False

    try:
        msg = MIMEMultipart("related")
        msg["Subject"] = f"🚨 EMERGENCY ALERT: Fall Detected for {user_name}!"
        msg["From"] = f"GuardianAI <{settings.MAIL_FROM}>"
        msg["To"] = to_email

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #ef4444;">
                <div style="text-align: center; border-bottom: 2px solid #ef4444; padding-bottom: 16px; margin-bottom: 20px;">
                    <h1 style="color: #ef4444; margin: 0; font-size: 24px;">🚨 FALL DETECTED ALERT</h1>
                    <p style="color: #94a3b8; font-size: 14px; margin-top: 4px;">GuardianAI Autonomous Safety System</p>
                </div>
                
                <p style="font-size: 16px; color: #f1f5f9;">Dear <b>{recipient_name}</b>,</p>
                
                <p style="font-size: 15px; color: #cbd5e1;">
                    A critical fall incident has been detected for <b>{user_name}</b> at <b>{incident_time}</b>.
                </p>

                <div style="background: #0f172a; padding: 16px; border-radius: 8px; border-left: 4px solid #ef4444; margin: 20px 0;">
                    <p style="margin: 4px 0; color: #94a3b8;"><b>Incident Details:</b></p>
                    <p style="margin: 4px 0; color: #f8fafc;">• <b>Detected At:</b> {incident_time}</p>
                    <p style="margin: 4px 0; color: #f8fafc;">• <b>AI Confidence:</b> {confidence * 100:.1f}%</p>
                    <p style="margin: 4px 0; color: #f8fafc;">• <b>Status:</b> Immediate Response Required</p>
                </div>

                {"<p style='color: #cbd5e1;'>A captured snapshot from the monitoring camera is attached below.</p>" if image_path and os.path.exists(image_path) else ""}

                <div style="margin-top: 30px; text-align: center;">
                    <p style="color: #64748b; font-size: 12px;">This is an automated safety alert from GuardianAI. Please verify and reach out immediately.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                img_data = f.read()
                image = MIMEImage(img_data, name=os.path.basename(image_path))
                msg.attach(image)

        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
        if settings.MAIL_STARTTLS:
            server.starttls()
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"✅ Emergency alert email successfully sent to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send emergency email to {to_email}: {e}")
        return False
