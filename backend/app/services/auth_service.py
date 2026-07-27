from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserRegister, UserLogin
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token


def register_user(db: Session, user: UserRegister):

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        return None

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        hashed_password=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def login_user(db: Session, user: UserLogin):

    db_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if not db_user:
        return None

    if not verify_password(
        user.password,
        db_user.hashed_password,
    ):
        return None

    token = create_access_token(
        {
            "sub": db_user.email,
            "id": db_user.id,
            "role": db_user.role,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": db_user,
    }