import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer

from app.database.base import Base


class SlotStatus(enum.Enum):
    AVAILABLE = "available"
    LIMITED = "limited"
    FULL = "full"


class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)

    # 🔥 THIS WAS MISSING
    vendor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    max_orders = Column(Integer, nullable=False)
    current_orders = Column(Integer, default=0)

    status = Column(Enum(SlotStatus), default=SlotStatus.AVAILABLE)
