from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.services.dashboard_service import get_dashboard_data

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/")
@router.get("/stats")
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = get_dashboard_data(db, current_user)

    return {
        "success": True,
        "total_incidents": data["total_incidents"],
        "today_incidents": data["today_incidents"],
        "active_contacts": data["total_contacts"],
        "last_incident": data["last_incident"],
        "system_status": "Active 🟢",
        "data": data,
    }