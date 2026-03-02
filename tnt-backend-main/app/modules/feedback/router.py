from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.modules.feedback.model import Feedback
from app.modules.orders.model import Order, OrderStatus
from app.modules.users.model import User

router = APIRouter(prefix="/feedback", tags=["Feedback"])


class FeedbackCreateRequest(BaseModel):
    quality_rating: int = Field(ge=1, le=5)
    time_rating: int = Field(ge=1, le=5)
    behavior_rating: int = Field(ge=1, le=5)
    comment: str | None = None


@router.post("/orders/{order_id}")
def submit_feedback(
    order_id: int,
    body: FeedbackCreateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = db.query(User).filter(User.phone == user["phone"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.user_id != db_user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Feedback allowed only for completed orders")

    existing = db.query(Feedback).filter(Feedback.order_id == order_id, Feedback.user_id == db_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Feedback already submitted for this order")

    feedback = Feedback(
        order_id=order_id,
        user_id=db_user.id,
        vendor_id=order.vendor_id,
        quality_rating=body.quality_rating,
        time_rating=body.time_rating,
        behavior_rating=body.behavior_rating,
        comment=body.comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {"message": "Feedback submitted", "feedback_id": feedback.id}


@router.get("/me")
def my_feedback(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = db.query(User).filter(User.phone == user["phone"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    records = (
        db.query(Feedback)
        .filter(Feedback.user_id == db_user.id)
        .order_by(Feedback.created_at.desc())
        .all()
    )

    return [
        {
            "id": row.id,
            "order_id": row.order_id,
            "vendor_id": row.vendor_id,
            "quality_rating": row.quality_rating,
            "time_rating": row.time_rating,
            "behavior_rating": row.behavior_rating,
            "comment": row.comment,
            "created_at": row.created_at.isoformat(),
        }
        for row in records
    ]


@router.get("/vendors/{vendor_id}/summary")
def vendor_feedback_summary(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    requester = db.query(User).filter(User.phone == user["phone"]).first()
    if not requester:
        raise HTTPException(status_code=404, detail="User not found")

    role = (requester.role.value or "").lower()
    if role == "vendor" and requester.id != vendor_id:
        raise HTTPException(status_code=403, detail="Cannot view feedback summary for another vendor")
    if role not in {"vendor", "admin", "super_admin"}:
        raise HTTPException(status_code=403, detail="Access denied")

    summary = (
        db.query(
            func.count(Feedback.id).label("total_reviews"),
            func.avg(Feedback.quality_rating).label("avg_quality_rating"),
            func.avg(Feedback.time_rating).label("avg_time_rating"),
            func.avg(Feedback.behavior_rating).label("avg_behavior_rating"),
        )
        .filter(Feedback.vendor_id == vendor_id)
        .first()
    )

    total_reviews = int(summary.total_reviews or 0)
    if total_reviews == 0:
        return {
            "vendor_id": vendor_id,
            "total_reviews": 0,
            "avg_quality_rating": 0.0,
            "avg_time_rating": 0.0,
            "avg_behavior_rating": 0.0,
        }

    return {
        "vendor_id": vendor_id,
        "total_reviews": total_reviews,
        "avg_quality_rating": round(float(summary.avg_quality_rating), 2),
        "avg_time_rating": round(float(summary.avg_time_rating), 2),
        "avg_behavior_rating": round(float(summary.avg_behavior_rating), 2),
    }
