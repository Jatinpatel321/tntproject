from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.load_insights import get_load_label, is_express_pickup_eligible
from app.core.deps import get_db
from app.modules.menu.model import MenuItem
from app.modules.slots.model import Slot, SlotStatus
from app.modules.stationery.service_model import StationeryService
from app.modules.users.model import User, UserRole
from app.modules.vendors.schemas import (
    VendorMenuItemResponse,
    VendorResponse,
    VendorSlotResponse,
)

router = APIRouter(prefix="/vendors", tags=["Vendors"])


def _vendor_load_summary(vendor_id: int, db: Session) -> tuple[str, bool]:
    slots = db.query(Slot).filter(Slot.vendor_id == vendor_id).all()
    if not slots:
        return "LOW", False

    total_capacity = sum(slot.max_orders for slot in slots)
    total_orders = sum(slot.current_orders for slot in slots)
    load_label = get_load_label(total_orders, total_capacity)
    express_eligible = is_express_pickup_eligible(total_orders, total_capacity)
    return load_label, express_eligible

@router.get("/", response_model=list[VendorResponse])
def get_vendors(type: str = "food", db: Session = Depends(get_db)):
    """
    Get all vendors by type (food or stationery)
    """
    vendor_type = type.strip().lower()
    if vendor_type not in {"food", "stationery"}:
        raise HTTPException(status_code=400, detail="Invalid vendor type")

    vendors_query = db.query(User).filter(
        User.role == UserRole.VENDOR,
        User.is_approved == True,
        User.is_active == True,
    )

    if vendor_type == "food":
        food_vendor_ids = db.query(MenuItem.vendor_id).filter(MenuItem.is_available == True).distinct()
        vendors_query = vendors_query.filter(User.id.in_(food_vendor_ids))
    else:
        stationery_vendor_ids = (
            db.query(StationeryService.vendor_id)
            .filter(StationeryService.is_available == True)
            .distinct()
        )
        vendors_query = vendors_query.filter(User.id.in_(stationery_vendor_ids))

    vendors = vendors_query.all()

    response = []
    for vendor in vendors:
        live_load_label, express_pickup_eligible = _vendor_load_summary(vendor.id, db)
        response.append(
            {
                "id": vendor.id,
                "name": vendor.name,
                "description": f"Vendor {vendor.name or vendor.id}",
                "vendor_type": vendor_type,
                "is_approved": vendor.is_approved,
                "phone": vendor.phone,
                "is_open": True,
                "logo_url": None,
                "live_load_label": live_load_label,
                "express_pickup_eligible": express_pickup_eligible,
            }
        )

    return response


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    """
    Get single vendor details
    """
    vendor = db.query(User).filter(
        User.id == vendor_id,
        User.role == UserRole.VENDOR,
        User.is_approved == True,
    ).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    load_label, express_eligible = _vendor_load_summary(vendor.id, db)

    return {
        "id": vendor.id,
        "name": vendor.name,
        "description": f"Vendor {vendor.name or vendor.id}",
        "vendor_type": "food",
        "is_approved": vendor.is_approved,
        "phone": vendor.phone,
        "is_open": True,
        "logo_url": None,
        "live_load_label": load_label,
        "express_pickup_eligible": express_eligible,
    }


@router.get("/{vendor_id}/menu", response_model=list[VendorMenuItemResponse])
def get_vendor_menu(vendor_id: int, db: Session = Depends(get_db)):
    """
    Get vendor menu items
    """
    vendor = db.query(User).filter(
        User.id == vendor_id,
        User.role == UserRole.VENDOR,
        User.is_approved == True,
    ).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    menu_items = db.query(MenuItem).filter(
        MenuItem.vendor_id == vendor_id,
        MenuItem.is_available == True,
    ).all()

    return [
        {
            "id": item.id,
            "vendor_id": item.vendor_id,
            "name": item.name,
            "description": item.description,
            "price": item.price,
            "image_url": item.image_url,
            "is_available": item.is_available,
        }
        for item in menu_items
    ]


@router.get("/{vendor_id}/slots", response_model=list[VendorSlotResponse])
def get_vendor_slots(vendor_id: int, db: Session = Depends(get_db)):
    """
    Get vendor pickup slots
    """
    vendor = db.query(User).filter(
        User.id == vendor_id,
        User.role == UserRole.VENDOR,
        User.is_approved == True,
    ).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    slots = db.query(Slot).filter(Slot.vendor_id == vendor_id).all()

    return [
        {
            "id": slot.id,
            "vendor_id": slot.vendor_id,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "is_available": slot.status != SlotStatus.FULL and slot.current_orders < slot.max_orders,
            "max_orders": slot.max_orders,
            "current_orders": slot.current_orders,
            "load_label": get_load_label(slot.current_orders, slot.max_orders),
            "express_pickup_eligible": is_express_pickup_eligible(slot.current_orders, slot.max_orders),
        }
        for slot in slots
    ]
