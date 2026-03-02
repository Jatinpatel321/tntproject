from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from app.database.base import Base


class StationeryService(Base):
    __tablename__ = "stationery_services"

    id = Column(Integer, primary_key=True, index=True)

    vendor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String, nullable=False)          # Printing, Binding
    price_per_unit = Column(Integer, nullable=False)  # paise
    unit = Column(String, nullable=False)          # page, copy, job

    is_available = Column(Boolean, default=True)
