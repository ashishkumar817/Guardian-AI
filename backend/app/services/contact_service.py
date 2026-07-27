from sqlalchemy.orm import Session

from app.models.emergency_contact import EmergencyContact
from app.models.user import User


def create_contact(db: Session, user: User, contact):

    new_contact = EmergencyContact(
        user_id=user.id,
        name=contact.name,
        relationship=contact.relationship,
        phone=contact.phone,
        email=contact.email,
        priority=contact.priority,
    )

    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)

    return new_contact


def get_contacts(db: Session, user: User):

    return (
        db.query(EmergencyContact)
        .filter(EmergencyContact.user_id == user.id)
        .order_by(EmergencyContact.priority)
        .all()
    )

def update_contact(db: Session, user: User, contact_id: int, contact):

    db_contact = (
        db.query(EmergencyContact)
        .filter(
            EmergencyContact.id == contact_id,
            EmergencyContact.user_id == user.id,
        )
        .first()
    )

    if db_contact is None:
        return None

    update_data = contact.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_contact, key, value)

    db.commit()
    db.refresh(db_contact)

    return db_contact


def delete_contact(db: Session, user: User, contact_id: int):

    db_contact = (
        db.query(EmergencyContact)
        .filter(
            EmergencyContact.id == contact_id,
            EmergencyContact.user_id == user.id,
        )
        .first()
    )

    if db_contact is None:
        return False

    db.delete(db_contact)
    db.commit()

    return True