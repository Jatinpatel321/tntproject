import logging

from sqlalchemy.orm import Session

from app.core.sms import send_sms
from app.modules.notifications.model import Notification

logger = logging.getLogger("tnt.notifications")


def notify_user(
    user_id: int,
    phone: str,
    title: str,
    message: str,
    db: Session,
    send_sms_flag: bool = True
):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message
    )

    db.add(notification)
    db.flush()

    if send_sms_flag:
        try:
            send_sms(phone, message)
        except Exception:
            logger.exception("notification_sms_failed user_id=%s phone=%s", user_id, phone)

    return notification
