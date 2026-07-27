from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.schemas.contact import ContactCreate
from app.services.contact_service import (
    create_contact,
    get_contacts,
)
from fastapi import HTTPException
from app.schemas.contact import ContactUpdate
from app.services.contact_service import (
    update_contact,
    delete_contact,
)

router = APIRouter(
    prefix="/contacts",
    tags=["Emergency Contacts"],
)


@router.post("/")
def add_contact(
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    new_contact = create_contact(
        db,
        current_user,
        contact,
    )

    return {
        "success": True,
        "message": "Contact added successfully",
        "data": new_contact,
    }


@router.get("/")
def list_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    contacts = get_contacts(
        db,
        current_user,
    )

    return {
        "success": True,
        "count": len(contacts),
        "data": contacts,
    }

@router.put("/{contact_id}")
def edit_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    updated = update_contact(
        db,
        current_user,
        contact_id,
        contact,
    )

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    return {
        "success": True,
        "message": "Contact updated successfully",
        "data": updated,
    }

@router.delete("/{contact_id}")
def remove_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    deleted = delete_contact(
        db,
        current_user,
        contact_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    return {
        "success": True,
        "message": "Contact deleted successfully",
    }