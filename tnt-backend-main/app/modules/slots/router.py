from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.faculty_policy import is_slot_in_faculty_priority_window
from app.core.load_insights import get_load_label, is_express_pickup_eligible
from app.core.security import get_current_user, require_role
from app.core.university_policy import get_university_policy
from app.modules.slots.model import Slot, SlotStatus
from app.modules.slots.schemas import SlotCreate, SlotResponse
from app.modules.slots.service import book_slot
from app.modules.users.model import User

router = APIRouter(prefix="/slots", tags=["Slots"])


@router.post("/", response_model=SlotResponse)
def create_slot(
    slot: SlotCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor"))
):
    if slot.end_time <= slot.start_time:
        raise HTTPException(status_code=400, detail="Invalid slot timing")

    policy = get_university_policy()
    if policy.get("enabled", False):
        duration_minutes = int((slot.end_time - slot.start_time).total_seconds() // 60)
        if duration_minutes < int(policy.get("min_slot_duration_minutes", 15)):
            raise HTTPException(
                status_code=400,
                detail="Slot duration violates university policy",
            )

    # Query the user to get the ID
    db_user = db.query(User).filter(User.phone == user["phone"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.is_approved:
        raise HTTPException(status_code=403, detail="Vendor not approved")

    new_slot = Slot(
        vendor_id=db_user.id,
        start_time=slot.start_time,
        end_time=slot.end_time,
        max_orders=slot.max_orders,
        current_orders=0,
        status=SlotStatus.AVAILABLE
    )

    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)

    return {
        "id": new_slot.id,
        "vendor_id": new_slot.vendor_id,
        "start_time": new_slot.start_time,
        "end_time": new_slot.end_time,
        "max_orders": new_slot.max_orders,
        "current_orders": new_slot.current_orders,
        "status": new_slot.status,
        "load_label": get_load_label(new_slot.current_orders, new_slot.max_orders),
        "express_pickup_eligible": is_express_pickup_eligible(new_slot.current_orders, new_slot.max_orders),
    }

@router.post("/{slot_id}/book")
def book(slot_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_user = db.query(User).filter(User.phone == user["phone"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    role = (db_user.role.value or "").lower()
    if is_slot_in_faculty_priority_window(slot.start_time.hour) and role not in {"faculty", "admin", "super_admin"}:
        raise HTTPException(status_code=403, detail="This slot is reserved for faculty during priority window")

    slot = book_slot(slot_id, db)
    return {
        "message": "Slot booked",
        "slot_id": slot.id,
        "current_orders": slot.current_orders,
        "status": slot.status,
        "load_label": get_load_label(slot.current_orders, slot.max_orders),
        "express_pickup_eligible": is_express_pickup_eligible(slot.current_orders, slot.max_orders),
    }
