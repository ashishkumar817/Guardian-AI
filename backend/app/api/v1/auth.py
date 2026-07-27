from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.database.database import get_db
from app.schemas.password import ForgotPasswordRequest
from app.services.password_service import create_password_otp
from app.services.email_service import send_otp_email
from app.schemas.password import VerifyOTPRequest
from app.services.password_service import verify_password_otp
from app.schemas.password import ResetPasswordRequest
from app.services.password_service import reset_user_password

from app.schemas.user import (
    UserRegister,
    UserLogin,
)

from app.services.auth_service import (
    register_user,
    login_user,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register")
def register(
    user: UserRegister,
    db: Session = Depends(get_db),
):

    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match",
        )

    created_user = register_user(db, user)

    if created_user is None:
        raise HTTPException(
            status_code=400,
            detail="Email already exists",
        )

    return {
        "success": True,
        "message": "User registered successfully",
        "data": {
            "id": created_user.id,
            "full_name": created_user.full_name,
            "email": created_user.email,
        },
    }


@router.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db),
):

    logged_in = login_user(db, user)

    if logged_in is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    return {
        "success": True,
        "message": "Login successful",
        "access_token": logged_in["access_token"],
        "token_type": "bearer",
        "user": {
            "id": logged_in["user"].id,
            "full_name": logged_in["user"].full_name,
            "email": logged_in["user"].email,
            "role": logged_in["user"].role,
        },
    }

@router.get("/me")
def get_profile(
    current_user: User = Depends(get_current_user),
):
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone": current_user.phone,
            "role": current_user.role,
            "is_active": current_user.is_active,
        }
    }

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):

    otp = create_password_otp(db, request.email)

    if otp is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    await send_otp_email(request.email, otp)

    return {
        "success": True,
        "message": "OTP sent successfully"
    }

@router.post("/verify-otp")
def verify_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db),
):

    valid = verify_password_otp(
        db,
        request.email,
        request.otp,
    )

    if not valid:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP",
        )

    return {
        "success": True,
        "message": "OTP verified successfully",
    }

@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):

    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match",
        )

    success = reset_user_password(
        db,
        request.email,
        request.otp,
        request.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP",
        )

    return {
        "success": True,
        "message": "Password reset successfully",
    }