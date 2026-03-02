from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from app.database.base import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)

    vendor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Integer, nullable=False)  # paise

    image_url = Column(String, nullable=False)  # 🔥 REQUIRED
    is_available = Column(Boolean, default=True)
