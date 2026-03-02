import time

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.redis import redis_client
from app.modules.slots.model import Slot, SlotStatus

LOCK_TTL = 5  # seconds


def _book_slot_internal(slot_id: int, db: Session, commit: bool):
    lock_key = f"slot_lock:{slot_id}"

    lock_acquired = redis_client.set(
        lock_key,
        "locked",
        nx=True,
        ex=LOCK_TTL
    )

    if not lock_acquired:
        raise HTTPException(
            status_code=429,
            detail="Slot is being booked, try again"
        )

    try:
        slot = db.query(Slot).filter(Slot.id == slot_id).with_for_update().first()

        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")

        if slot.current_orders >= slot.max_orders:
            slot.status = SlotStatus.FULL
            if commit:
                db.commit()
            else:
                db.flush()
            raise HTTPException(status_code=400, detail="Slot full")

        slot.current_orders += 1
        slot.congestion_level = (slot.current_orders / slot.max_orders) * 100

        if slot.current_orders >= slot.max_orders:
            slot.status = SlotStatus.FULL
        elif slot.current_orders >= int(slot.max_orders * 0.7):
            slot.status = SlotStatus.LIMITED

        if commit:
            db.commit()
            db.refresh(slot)
        else:
            db.flush()

        return slot

    finally:
        redis_client.delete(lock_key)


def book_slot(slot_id: int, db: Session):
    return _book_slot_internal(slot_id, db, commit=True)


def reserve_slot_for_order(slot_id: int, db: Session):
    return _book_slot_internal(slot_id, db, commit=False)
