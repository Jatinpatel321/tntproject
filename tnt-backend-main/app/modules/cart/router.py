import json
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.load_insights import get_load_label, is_express_pickup_eligible
from app.core.redis import redis_client
from app.core.security import get_current_user
from app.modules.menu.model import MenuItem
from app.modules.orders.checkout_service import checkout_order_for_user
from app.modules.orders.item_schemas import OrderItemCreate
from app.modules.payments.service import initiate_payment
from app.modules.users.model import User, UserRole

router = APIRouter(prefix="/cart", tags=["Cart"])


class SoloCartItemRequest(BaseModel):
    menu_item_id: int
    quantity: int = Field(default=1, gt=0)


def _cart_key(user_id: int) -> str:
    return f"tnt:cart:user:{user_id}"


def _get_cart(user_id: int) -> dict:
    raw = redis_client.get(_cart_key(user_id))
    if not raw:
        return {"vendor_id": None, "items": []}

    try:
        cart = json.loads(raw)
        if not isinstance(cart, dict):
            return {"vendor_id": None, "items": []}
        return {
            "vendor_id": cart.get("vendor_id"),
            "items": cart.get("items", []),
        }
    except Exception:
        return {"vendor_id": None, "items": []}


def _save_cart(user_id: int, cart: dict) -> None:
    redis_client.setex(_cart_key(user_id), 60 * 60 * 12, json.dumps(cart))


def _cart_response(cart: dict) -> dict:
    total_amount = sum(int(item["price"]) * int(item["quantity"]) for item in cart["items"])
    total_items = sum(int(item["quantity"]) for item in cart["items"])
    return {
        "vendor_id": cart.get("vendor_id"),
        "items": cart.get("items", []),
        "total_items": total_items,
        "total_amount": total_amount,
    }


def _checkout_order_from_cart(slot_id: int, db_user: User, db: Session) -> tuple[dict, int]:
    cart = _get_cart(db_user.id)
    if not cart["items"]:
        raise HTTPException(status_code=400, detail="Cart is empty")

    items = [
        OrderItemCreate(menu_item_id=int(item["menu_item_id"]), quantity=int(item["quantity"]))
        for item in cart["items"]
    ]
    order, slot, total_amount, eta_minutes = checkout_order_for_user(db_user, slot_id, items, db)

    redis_client.delete(_cart_key(db_user.id))

    return {
        "order_id": order.id,
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "total_amount": total_amount,
        "eta_minutes": eta_minutes,
        "pickup_load_label": get_load_label(slot.current_orders, slot.max_orders),
        "express_pickup_eligible": is_express_pickup_eligible(slot.current_orders, slot.max_orders),
    }, order.id


@router.get("/")
def get_cart(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = db.query(User).filter(User.phone == user["phone"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    cart = _get_cart(db_user.id)
    return _cart_response(cart)


@router.post("/items")
def add_cart_item(
    payload: SoloCartItemRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = db.query(User).filter(User.phone == user["phone"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    menu_item = db.query(MenuItem).filter(MenuItem.id == payload.menu_item_id).first()
    if not menu_item:
        raise HTTPException(status_code=400, detail="Menu item not found")
    if not menu_item.is_available:
        raise HTTPException(status_code=400, detail="Menu item not available")

    vendor = db.query(User).filter(User.id == menu_item.vendor_id).first()
    if not vendor or vendor.role != UserRole.VENDOR or not vendor.is_active or not vendor.is_approved:
        raise HTTPException(status_code=400, detail="Vendor is not available")

    cart = _get_cart(db_user.id)

    existing_vendor_id = cart.get("vendor_id")
    if existing_vendor_id is not None and int(existing_vendor_id) != int(menu_item.vendor_id):
        raise HTTPException(status_code=400, detail="Cannot add items from multiple vendors")

    updated = False
    for item in cart["items"]:
        if int(item["menu_item_id"]) == int(payload.menu_item_id):
            item["quantity"] = int(item["quantity"]) + int(payload.quantity)
            updated = True
            break

    if not updated:
        cart["items"].append(
            {
                "menu_item_id": menu_item.id,
                "name": menu_item.name,
                "price": int(menu_item.price),
                "quantity": int(payload.quantity),
            }
        )

    cart["vendor_id"] = int(menu_item.vendor_id)
    _save_cart(db_user.id, cart)

    return _cart_response(cart)


@router.delete("/items/{menu_item_id}")
def remove_cart_item(
    menu_item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = db.query(User).filter(User.phone == user["phone"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    cart = _get_cart(db_user.id)
    before_count = len(cart["items"])
    cart["items"] = [item for item in cart["items"] if int(item["menu_item_id"]) != int(menu_item_id)]
    if len(cart["items"]) == before_count:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if not cart["items"]:
        cart["vendor_id"] = None

    _save_cart(db_user.id, cart)
    return _cart_response(cart)


@router.delete("/")
def clear_cart(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = db.query(User).filter(User.phone == user["phone"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    redis_client.delete(_cart_key(db_user.id))
    return {"message": "Cart cleared"}


@router.post("/checkout/{slot_id}")
def checkout_cart(
    slot_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = db.query(User).filter(User.phone == user["phone"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    response, _ = _checkout_order_from_cart(slot_id, db_user, db)
    return response


@router.post("/checkout/{slot_id}/pay")
def checkout_and_initiate_payment(
    slot_id: int,
    checkout_idempotency_key: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = db.query(User).filter(User.phone == user["phone"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    idempotency_cache_key = None
    if checkout_idempotency_key:
        idempotency_cache_key = f"tnt:checkout_pay:{db_user.id}:{checkout_idempotency_key}"
        cached = redis_client.get(idempotency_cache_key)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                pass

    checkout_response, order_id = _checkout_order_from_cart(slot_id, db_user, db)

    response = {
        "order_created": True,
        "payment_initiated": False,
        "order": checkout_response,
        "payment": None,
        "payment_error": None,
    }

    try:
        payment_response = initiate_payment(order_id=order_id, user=user, db=db)
        response["payment_initiated"] = True
        response["payment"] = payment_response
    except HTTPException as exc:
        response["payment_error"] = {
            "status_code": exc.status_code,
            "detail": exc.detail,
        }
    except Exception as exc:
        response["payment_error"] = {
            "status_code": 500,
            "detail": str(exc),
        }

    if idempotency_cache_key:
        redis_client.setex(idempotency_cache_key, 3600, json.dumps(response))

    return response
