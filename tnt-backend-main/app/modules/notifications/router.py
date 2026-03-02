from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.modules.notifications.model import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/")
def get_notifications(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    from app.modules.users.model import User
    db_user = db.query(User).filter(User.phone == user["phone"]).first()

    return (
        db.query(Notification)
        .filter(Notification.user_id == db_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.post("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    from app.modules.users.model import User
    db_user = db.query(User).filter(User.phone == user["phone"]).first()

    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == db_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()

    return {"message": "Notification marked as read"}
