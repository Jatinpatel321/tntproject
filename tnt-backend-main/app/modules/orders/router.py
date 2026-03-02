from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user, require_role
from app.modules.orders import order_service
from app.modules.orders.history_schemas import OrderHistoryResponse
from app.modules.orders.item_schemas import OrderItemCreate
from app.modules.orders.schemas import OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


# 🧾 PLACE ORDER (WITH ITEMS)
@router.post("/{slot_id}")
def place_order(
    slot_id: int,
    items: list[OrderItemCreate],
    idempotency_key: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, Any]:
    return order_service.place_order(user, slot_id, items, idempotency_key, db)


# 👤 STUDENT — MY ORDERS
@router.get("/my", response_model=list[OrderResponse])
def my_orders(db: Session = Depends(get_db), user=Depends(get_current_user)) -> list[OrderResponse]:
    return order_service.get_my_orders(user, db)


# 📊 VENDOR — ANALYTICS DASHBOARD
@router.get("/vendor/analytics")
def vendor_analytics(
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
) -> dict[str, Any]:
    """Return aggregated order analytics for the authenticated vendor.

    Includes total/pending/confirmed/ready/completed/cancelled counts,
    revenue, completion rate, average confirmation latency, and peak
    hour/day breakdowns.
    """
    return order_service.get_vendor_analytics(user, db)


# 🧑‍🍳 VENDOR — INCOMING ORDERS
@router.get("/vendor", response_model=list[OrderResponse])
def vendor_orders(db: Session = Depends(get_db), user=Depends(require_role("vendor"))) -> list[OrderResponse]:
    return order_service.get_vendor_orders(user, db)


# ✅ VENDOR — CONFIRM ORDER
@router.post("/{order_id}/confirm")
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
) -> dict[str, Any]:
    return order_service.confirm_order(user, order_id, db)


# ✅ VENDOR — MARK ORDER READY
@router.post("/{order_id}/ready")
def ready_order(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
) -> dict[str, Any]:
    return order_service.mark_order_ready(user, order_id, db)


# ❌ STUDENT — CANCEL ORDER
@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, Any]:
    return order_service.cancel_order(user, order_id, db)


# 🕒 ORDER TIMELINE
@router.get("/{order_id}/timeline", response_model=list[OrderHistoryResponse])
def order_timeline(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> list[OrderHistoryResponse]:
    return order_service.get_order_timeline(user, order_id, db)


@router.post("/{order_id}/reorder")
def reorder_order(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, Any]:
    return order_service.reorder(user, order_id, db)


@router.get("/{order_id}/eta")
def order_eta(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, Any]:
    return order_service.get_order_eta(user, order_id, db)


# 🧾 VENDOR — ORDER DETAILS
@router.get("/vendor/{order_id}")
def vendor_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
) -> dict[str, Any]:
    return order_service.get_vendor_order_detail(user, order_id, db)


# 📱 QR PICKUP ENDPOINTS

@router.post("/{order_id}/qr", response_model=dict)
def generate_qr_endpoint(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate QR code for order pickup."""
    return order_service.generate_order_qr(order_id, db)


@router.post("/qr/pickup/confirm", response_model=dict)
@router.post("/qr/confirm", response_model=dict)
def confirm_pickup_endpoint(
    qr_code: str,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    """Confirm pickup using QR code."""
    return order_service.confirm_qr_pickup(user, qr_code, db)


@router.get("/qr/{qr_code}", response_model=dict)
def get_order_by_qr_endpoint(
    qr_code: str,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    """Get order details by QR code for vendor verification."""
    return order_service.get_order_by_qr_code(user, qr_code, db)
