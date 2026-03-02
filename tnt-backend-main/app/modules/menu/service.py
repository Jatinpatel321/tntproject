from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.menu.model import MenuItem


def create_menu_item(vendor_id: int, data, db: Session):
    item = MenuItem(
        vendor_id=vendor_id,
        name=data.name,
        description=data.description,
        price=data.price
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_vendor_menu(vendor_id: int, db: Session):
    return db.query(MenuItem).filter(
        MenuItem.vendor_id == vendor_id,
        MenuItem.is_available == True
    ).all()
