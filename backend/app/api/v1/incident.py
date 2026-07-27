from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.schemas.incident import IncidentCreate
from app.services.incident_service import (
    create_incident,
    get_incidents,
)

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


@router.post("/")
def add_incident(
    incident: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    new_incident = create_incident(
        db=db,
        user=current_user,
        confidence=incident.confidence,
        image_path=incident.image_path,
    )

    return {
        "success": True,
        "message": "Incident created successfully",
        "data": new_incident,
    }


@router.get("/")
def list_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    incidents = get_incidents(
        db,
        current_user,
    )

    return {
        "success": True,
        "count": len(incidents),
        "data": incidents,
    }