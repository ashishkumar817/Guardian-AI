from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.user import User


def create_incident(
    db: Session,
    user: User,
    confidence: float,
    image_path: str | None,
):

    incident = Incident(
        user_id=user.id,
        confidence=confidence,
        image_path=image_path,
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident


def get_incidents(
    db: Session,
    user: User,
):

    return (
        db.query(Incident)
        .filter(Incident.user_id == user.id)
        .order_by(Incident.detected_at.desc())
        .all()
    )