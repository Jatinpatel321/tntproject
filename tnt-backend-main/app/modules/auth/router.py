from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.observability import observability
from app.core.rate_limit import login_rate_limiter, otp_rate_limiter
from app.core.security import create_access_token
from app.modules.auth.otp_service import generate_otp, verify_otp
from app.modules.auth.schemas import LoginRequest, VerifyOTPRequest
from app.modules.users.model import User, UserRole

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/send-otp")
async def send_otp(
    body: LoginRequest,
    _rl: None = Depends(otp_rate_limiter),
):
    # generate_otp handles Redis storage + SMS delivery internally.
    # The returned OTP value is intentionally unused here — it must never
    # be echoed back to the client.
    generate_otp(body.phone)
    return {"message": "OTP sent"}

@router.post("/verify-otp")
def verify_otp_login(
    body: VerifyOTPRequest,
    db: Session = Depends(get_db),
    _rl: None = Depends(login_rate_limiter),
):
    if not verify_otp(body.phone, body.otp):
        observability.record_otp_attempt(success=False)
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    observability.record_otp_attempt(success=True)

    user = db.query(User).filter(User.phone == body.phone).first()

    # 🔥 AUTO-REGISTER IF NEW USER
    if not user:
        user = User(
            phone=body.phone,
            role=UserRole.STUDENT  # default role
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(
        data={
            "sub": str(user.id),
            "phone": user.phone,
            "role": user.role.value
        },
        expires_delta=60
    )

    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "phone": user.phone,
                "name": user.name,
                "role": user.role.value,
                "university_id": user.university_id,
                "is_active": user.is_active,
                "is_approved": user.is_approved
            },
            "is_new_user": user.name is None
        }
    }
