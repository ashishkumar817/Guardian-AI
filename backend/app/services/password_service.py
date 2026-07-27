from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.user import User
from app.models.password_otp import PasswordOTP
from app.utils.otp import generate_otp
from app.auth.hashing import hash_password


def create_password_otp(db: Session, email: str):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    # Remove previous unused OTPs
    db.query(PasswordOTP).filter(
        PasswordOTP.email == email,
        PasswordOTP.is_used == False
    ).delete()

    otp = generate_otp()

    otp_record = PasswordOTP(
        email=email,
        otp=otp,
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        is_used=False
    )

    db.add(otp_record)
    db.commit()

    return otp

def verify_password_otp(db: Session, email: str, otp: str):

    otp_record = (
        db.query(PasswordOTP)
        .filter(
            PasswordOTP.email == email,
            PasswordOTP.otp == otp,
            PasswordOTP.is_used == False
        )
        .first()
    )

    if otp_record is None:
        return False

    if otp_record.expires_at < datetime.utcnow():
        return False

    return True



def reset_user_password(
    db: Session,
    email: str,
    otp: str,
    new_password: str,
):

    otp_record = (
        db.query(PasswordOTP)
        .filter(
            PasswordOTP.email == email,
            PasswordOTP.otp == otp,
            PasswordOTP.is_used == False
        )
        .first()
    )

    if otp_record is None:
        return False

    if otp_record.expires_at < datetime.utcnow():
        return False

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        return False

    user.hashed_password = hash_password(new_password)

    otp_record.is_used = True

    db.commit()

    return True