from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.emergency_contact import EmergencyContact
from app.models.user import User


def get_dashboard_data(db: Session, user: User):
    today = datetime.now(timezone.utc).date()

    total_incidents = (
        db.query(Incident)
        .filter(Incident.user_id == user.id)
        .count()
    )

    today_incidents = (
        db.query(Incident)
        .filter(
            Incident.user_id == user.id,
            func.date(Incident.detected_at) == today,
        )
        .count()
    )

    total_contacts = (
        db.query(EmergencyContact)
        .filter(EmergencyContact.user_id == user.id)
        .count()
    )

    last_incident = (
        db.query(Incident)
        .filter(Incident.user_id == user.id)
        .order_by(Incident.detected_at.desc())
        .first()
    )

    return {
        "total_incidents": total_incidents,
        "today_incidents": today_incidents,
        "total_contacts": total_contacts,
        "last_incident": last_incident,
    }