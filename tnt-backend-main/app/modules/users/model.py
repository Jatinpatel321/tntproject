import enum

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from app.core.time_utils import utcnow_naive
from app.database.base import Base


class UserRole(enum.Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    VENDOR = "vendor"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    vendor_type = Column(String, nullable=False, default="food")
    university_id = Column(String, nullable=True)

    # inside User model
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)  # 🔥 for vendors
    preferences = Column(JSON, default=dict)  # 🔥 for user preferences
    created_at = Column(DateTime, default=utcnow_naive)

    owned_groups = relationship("Group", back_populates="owner")
    group_memberships = relationship("GroupMember", back_populates="user")
