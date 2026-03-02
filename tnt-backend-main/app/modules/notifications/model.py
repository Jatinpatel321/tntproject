from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.core.time_utils import utcnow_naive
from app.database.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String, nullable=False)
    message = Column(String, nullable=False)

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow_naive)
