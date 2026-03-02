from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.db_transaction import transactional
from app.core.faculty_policy import is_slot_in_faculty_priority_window
from app.core.time_utils import utcnow_naive
from app.core.university_policy import get_university_policy, is_hour_in_break_window
from app.modules.orders.item_schemas import OrderItemCreate
from app.modules.orders.item_service import add_items_to_order
from app.modules.orders.model import Order, OrderStatus
from app.modules.orders.service import create_order
from app.modules.slots.model import Slot
from app.modules.slots.service import reserve_slot_for_order
from app.modules.users.model import User


@transactional
def checkout_order_for_user(
    db_user: User,
    slot_id: int,
    items: list[OrderItemCreate],
    db: Session,
):
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    vendor = db.query(User).filter(User.id == slot.vendor_id).first()
    if not vendor or not vendor.is_active or not vendor.is_approved:
        raise HTTPException(status_code=400, detail="Vendor is not available")

    role = (db_user.role.value or "").lower()
    if is_slot_in_faculty_priority_window(slot.start_time.hour) and role not in {"faculty", "admin", "super_admin"}:
        raise HTTPException(status_code=403, detail="This slot is reserved for faculty during priority window")

    policy = get_university_policy()
    if policy.get("enabled", False):
        if not is_hour_in_break_window(
            slot.start_time.hour,
            int(policy.get("break_start_hour", 12)),
            int(policy.get("break_end_hour", 14)),
        ):
            raise HTTPException(status_code=400, detail="Orders are allowed only during university break window")

        now = utcnow_naive()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        existing_orders = (
            db.query(Order)
            .filter(
                Order.user_id == db_user.id,
                Order.created_at >= day_start,
                Order.created_at < day_end,
                Order.status != OrderStatus.CANCELLED,
            )
            .count()
        )
        if existing_orders >= int(policy.get("max_orders_per_user", 3)):
            raise HTTPException(status_code=400, detail="Maximum orders per user reached for this day")

    if items:
        menu_vendor_ids = set()
        for item in items:
            from app.modules.menu.model import MenuItem

            menu_item = db.query(MenuItem).filter(MenuItem.id == item.menu_item_id).first()
            if not menu_item:
                raise HTTPException(status_code=400, detail=f"Menu item {item.menu_item_id} not found")
            if not menu_item.is_available:
                raise HTTPException(status_code=400, detail=f"Menu item {item.menu_item_id} not available")
            menu_vendor_ids.add(menu_item.vendor_id)

        if len(menu_vendor_ids) > 1:
            raise HTTPException(status_code=400, detail="Cannot order from multiple vendors")

    # All writes below are flushed to the session; the @transactional decorator
    # issues the final db.commit() (or db.rollback() on crash) so this entire
    # checkout lands in a single atomic transaction.
    slot = reserve_slot_for_order(slot_id, db)

    order = create_order(
        user_id=db_user.id,
        slot_id=slot_id,
        db=db,
    )

    total_amount = add_items_to_order(order, items, db)
    order.total_amount = total_amount

    congestion_factor = slot.congestion_level if hasattr(slot, "congestion_level") else 0
    base_eta = 15
    eta_minutes = base_eta + int(congestion_factor / 10)
    order.eta_minutes = eta_minutes

    return order, slot, total_amount, eta_minutes
