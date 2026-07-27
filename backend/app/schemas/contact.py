from typing import Optional
from pydantic import BaseModel, EmailStr


class ContactCreate(BaseModel):
    name: str
    relationship: str
    phone: str
    email: Optional[EmailStr] = None
    priority: int = 1


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    relationship: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    priority: Optional[int] = None


class ContactResponse(BaseModel):
    id: int
    name: str
    relationship: str
    phone: str
    email: Optional[str] = None
    priority: int

    model_config = {
        "from_attributes": True
    }