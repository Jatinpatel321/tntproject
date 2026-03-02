from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.rate_limit import payment_rate_limiter
from app.core.security import get_current_user
from app.modules.payments import payment_service

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
    dependencies=[Depends(payment_rate_limiter)],
)


@router.post("/razorpay/initiate/{order_id}")
def initiate(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    x_idempotency_key: str | None = Header(None, alias="X-Idempotency-Key"),
):
    """Initiate a Razorpay payment.

    Send a ``X-Idempotency-Key: <uuid>`` header to make this endpoint safe
    to retry.  Repeated calls with the same key return the existing payment
    record without creating a second Razorpay order.
    """
    return payment_service.initiate(order_id, user, x_idempotency_key, db)


@router.post("/razorpay/verify/{payment_id}")
def verify(
    payment_id: int,
    razorpay_payment_id: str,
    razorpay_signature: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return payment_service.verify(payment_id, razorpay_payment_id, razorpay_signature, user, db)


@router.post("/razorpay/refund/{payment_id}")
def refund(
    payment_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return payment_service.refund(payment_id, user, db)
