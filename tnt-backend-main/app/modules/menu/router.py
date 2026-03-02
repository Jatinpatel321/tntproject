from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.file_upload import save_menu_image
from app.core.security import get_current_user, require_role
from app.modules.menu.model import MenuItem
from app.modules.users.model import User, UserRole

router = APIRouter(prefix="/menu", tags=["Menu"])


@router.post("/")
def add_menu_item(
    name: str = Form(...),
    price: int = Form(...),
    description: str | None = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor"))
):
    db_user = db.query(User).filter(User.phone == user["phone"]).first()
    if (db_user.vendor_type or "food").lower() != "food":
        raise HTTPException(status_code=403, detail="Only food vendors can manage menu items")

    if not db_user.is_approved:
        raise HTTPException(status_code=403, detail="Vendor not approved")

    image_url = save_menu_image(image)

    item = MenuItem(
        vendor_id=db_user.id,
        name=name,
        description=description,
        price=price,
        image_url=image_url
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@router.get("/{vendor_id}")
def get_menu_items(vendor_id: int, db: Session = Depends(get_db)):
    """List menu items for a specific vendor"""
    items = db.query(MenuItem).filter(
        MenuItem.vendor_id == vendor_id,
        MenuItem.is_available == True
    ).all()

    # Check if vendor exists and is approved
    vendor = db.query(User).filter(
        User.id == vendor_id,
        User.role == UserRole.VENDOR,
        User.is_approved == True
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found or not approved")

    return items


@router.put("/{item_id}")
def update_menu_item(
    item_id: int,
    name: str = Form(None),
    price: int = Form(None),
    description: str | None = Form(None),
    is_available: bool = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor"))
):
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Ownership check
    db_user = db.query(User).filter(User.phone == user["phone"]).first()
    if (db_user.vendor_type or "food").lower() != "food":
        raise HTTPException(status_code=403, detail="Only food vendors can manage menu items")

    if item.vendor_id != db_user.id:
        raise HTTPException(status_code=403, detail="Cannot edit other vendor's menu")

    if name is not None:
        item.name = name
    if price is not None:
        item.price = price
    if description is not None:
        item.description = description
    if is_available is not None:
        item.is_available = is_available
    if image:
        item.image_url = save_menu_image(image)

    db.commit()
    return item
