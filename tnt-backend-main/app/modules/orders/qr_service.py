import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.core.time_utils import utcnow_naive
from app.modules.orders.model import Order, OrderStatus


def generate_qr_code(order_id: int, db: Session) -> str:
    """Generate a unique QR code for an order."""
    qr_code = str(uuid.uuid4())
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError("Order not found")

    # Accept both canonical READY and legacy READY_FOR_PICKUP
    if order.status not in (OrderStatus.READY, OrderStatus.READY_FOR_PICKUP):
        raise ValueError("Order is not ready for pickup")

    if order.qr_code:
        return order.qr_code  # Return existing QR if already generated

    order.qr_code = qr_code
    db.commit()
    return qr_code


def confirm_pickup(qr_code: str, vendor_id: int, db: Session) -> bool:
    """Confirm pickup using QR code."""
    order = db.query(Order).filter(Order.qr_code == qr_code).first()
    if not order:
        return False

    if order.vendor_id != vendor_id:
        return False  # Only the assigned vendor can confirm

    # Accept both canonical READY and legacy READY_FOR_PICKUP
    if order.status not in (OrderStatus.READY, OrderStatus.READY_FOR_PICKUP):
        return False

    order.status = OrderStatus.PICKED
    order.pickup_confirmed_at = utcnow_naive()
    order.pickup_confirmed_by = vendor_id
    db.commit()
    return True


def get_order_by_qr(qr_code: str, db: Session) -> Order:
    """Get order details by QR code for vendor verification."""
    return db.query(Order).filter(Order.qr_code == qr_code).first()
