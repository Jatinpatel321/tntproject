from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.orders.history_model import OrderHistory
from app.modules.orders.model import Order, OrderStatus
from app.modules.orders.state_machine import validate_transition
from app.modules.rewards.service import process_order_completion_rewards
from app.modules.slots.model import Slot


def create_order(user_id: int, slot_id: int, db: Session):
    slot = db.query(Slot).filter(Slot.id == slot_id).first()

    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    order = Order(
        user_id=user_id,
        slot_id=slot_id,
        vendor_id=slot.vendor_id,
        status=OrderStatus.PLACED
    )

    db.add(order)
    db.flush()
    db.refresh(order)

    return order


def update_order_status(
    order: Order,
    new_status: OrderStatus,
    actor_role: str,
    db: Session
):
    # ── State machine gate (always runs first) ────────────────────────────
    validate_transition(order.status, new_status)

    # ── Role-permission layer (runs after transition is confirmed valid) ──
    # Student rules
    if actor_role == "student":
        if new_status != OrderStatus.CANCELLED:
            raise HTTPException(
                status_code=403,
                detail="Students can only cancel orders"
            )

    # Vendor rules
    if actor_role == "vendor":
        allowed_vendor_targets = {
            OrderStatus.CONFIRMED,
            OrderStatus.READY,
            OrderStatus.PICKED,
            # legacy compat
            OrderStatus.COMPLETED,
            OrderStatus.READY_FOR_PICKUP,
        }
        if new_status not in allowed_vendor_targets:
            raise HTTPException(
                status_code=403,
                detail=f"Vendors cannot set orders to '{new_status.value}'"
            )

    # ✅ Apply the transition
    order.status = new_status

    # ✅ Record history
    history = OrderHistory(
        order_id=order.id,
        status=new_status
    )
    db.add(history)

    if new_status in (OrderStatus.READY, OrderStatus.PICKED, OrderStatus.COMPLETED):
        process_order_completion_rewards(order.id, db)
