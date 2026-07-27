from fastapi import FastAPI
from app.models.emergency_contact import EmergencyContact
from app.database.database import Base, engine
from app.models.user import User
from app.models.password_otp import PasswordOTP
from app.api.v1.auth import router as auth_router
from app.api.v1.contact import router as contact_router
from app.models.incident import Incident
from app.api.v1.incident import router as incident_router
from app.api.v1.dashboard import router as dashboard_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GuardianAI API",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(contact_router)
app.include_router(incident_router)
app.include_router(dashboard_router)

@app.get("/")
def root():
    return {
        "message": "GuardianAI Backend Running 🚀"
    }