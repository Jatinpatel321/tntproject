from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from sqlalchemy import func

from app.core.deps import get_db
from app.core.emergency import set_emergency_shutdown
from app.core.faculty_policy import get_faculty_priority_policy, set_faculty_priority_policy
from app.core.security import require_role
from app.core.time_utils import utcnow_naive
from app.core.university_policy import get_university_policy, set_university_policy
from app.modules.ledger.model import Ledger
from app.modules.orders.model import Order, OrderStatus
from app.modules.payments.model import Payment, PaymentStatus
from app.modules.users.model import User, UserRole

router = APIRouter(prefix="/admin", tags=["Admin"])


# 👀 VIEW ALL VENDORS
@router.get("/vendors")
def list_vendors(
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
):
    return jsonable_encoder(db.query(User).filter(User.role == UserRole.VENDOR).all())


# ✅ APPROVE VENDOR
@router.post("/vendors/{vendor_id}/approve")
def approve_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
) -> dict[str, Any]:
    vendor = db.query(User).filter(User.id == vendor_id).first()
    if not vendor or vendor.role != UserRole.VENDOR:
        raise HTTPException(status_code=404, detail="Vendor not found")

    vendor.is_approved = True
    vendor.is_active = True
    db.commit()

    return {"message": "Vendor approved", "vendor_id": vendor_id}


# 🚫 REJECT VENDOR
@router.post("/vendors/{vendor_id}/reject")
def reject_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
) -> dict[str, Any]:
    """Reject (or un-approve) a vendor application.

    Sets ``is_approved=False`` and ``is_active=False`` so the vendor cannot
    log in or appear in any public listing until explicitly re-approved.
    """
    vendor = db.query(User).filter(User.id == vendor_id).first()
    if not vendor or vendor.role != UserRole.VENDOR:
        raise HTTPException(status_code=404, detail="Vendor not found")

    vendor.is_approved = False
    vendor.is_active = False
    db.commit()

    # Best-effort notification
    try:
        from app.modules.notifications.service import notify_user
        notify_user(
            user_id=vendor.id,
            phone=vendor.phone,
            title="Application Status Update",
            message="Your vendor application has been rejected. Contact admin for details.",
            db=db,
        )
        db.commit()
    except Exception:
        pass

    return {"message": "Vendor rejected", "vendor_id": vendor_id}


# 🚫 BLOCK / UNBLOCK USER
@router.post("/users/{user_id}/toggle")
def toggle_user(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
) -> dict[str, Any]:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.is_active = not db_user.is_active
    db.commit()

    return {
        "user_id": user_id,
        "is_active": db_user.is_active
    }


# 📦 VIEW ALL ORDERS
@router.get("/orders")
def all_orders(
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
):
    return jsonable_encoder(db.query(Order).order_by(Order.created_at.desc()).all())


# 📘 VIEW LEDGER
@router.get("/ledger")
def ledger_view(
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
):
    return jsonable_encoder(db.query(Ledger).order_by(Ledger.created_at.desc()).all())


# 🚨 EMERGENCY SHUTDOWN
@router.post("/shutdown")
def emergency_shutdown(
    enabled: bool,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
) -> dict[str, Any]:
    """Enable/disable emergency shutdown mode"""
    is_enabled = set_emergency_shutdown(enabled)
    return {
        "message": f"Emergency shutdown {'enabled' if is_enabled else 'disabled'}",
        "enabled": is_enabled,
    }


# 🚩 MARK ORDER AS FRAUD
@router.post("/orders/{order_id}/fraud")
def mark_order_fraud(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
) -> dict[str, Any]:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.fraud_flag:
        raise HTTPException(status_code=400, detail="Order is already flagged as fraud")

    order.fraud_flag = True
    order.flagged_at = utcnow_naive()
    db.commit()

    return {
        "message": "Order marked as fraud",
        "order_id": order.id,
        "flagged_at": order.flagged_at.isoformat(),
    }


# 📊 ANALYTICS ENDPOINT
@router.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
) -> dict[str, Any]:
    """Comprehensive admin analytics dashboard.

    Returns seven sections:
    - ``totals``          — snapshot counts across all entities
    - ``orders_by_day``   — daily order volume for last 30 days (time-series)
    - ``revenue_by_day``  — daily revenue (paise) for last 30 days (time-series)
    - ``signups_by_day``  — new user registrations per day for last 30 days
    - ``order_status``    — count breakdown by OrderStatus value
    - ``payment_status``  — count breakdown by PaymentStatus value
    - ``top_vendors``     — top 10 vendors ranked by order volume
    - ``peak_hours``      — order count per hour-of-day (0-23) across all time
    - ``week_comparison`` — this week vs previous week (orders + revenue)
    - ``fraud_stats``     — total flagged orders and flagged-order rate
    """
    from datetime import timedelta

    now = utcnow_naive()
    thirty_days_ago = now - timedelta(days=30)
    this_week_start = now - timedelta(days=7)
    last_week_start = now - timedelta(days=14)

    # ── Totals ────────────────────────────────────────────────────────────
    total_users = db.query(User).count()
    total_vendors = db.query(User).filter(User.role == UserRole.VENDOR).count()
    total_students = db.query(User).filter(User.role == UserRole.STUDENT).count()
    total_orders = db.query(Order).count()
    total_revenue_paise = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == PaymentStatus.SUCCESS
    ).scalar() or 0

    # ── Orders by day (last 30 days) ──────────────────────────────────────
    orders_by_day_rows = db.query(
        func.strftime("%Y-%m-%d", Order.created_at).label("day"),
        func.count(Order.id).label("count"),
    ).filter(Order.created_at >= thirty_days_ago)\
     .group_by(func.strftime("%Y-%m-%d", Order.created_at))\
     .order_by(func.strftime("%Y-%m-%d", Order.created_at))\
     .all()
    orders_by_day = [{"date": r.day, "orders": r.count} for r in orders_by_day_rows]

    # ── Revenue by day (last 30 days) ─────────────────────────────────────
    revenue_by_day_rows = db.query(
        func.strftime("%Y-%m-%d", Payment.created_at).label("day"),
        func.coalesce(func.sum(Payment.amount), 0).label("revenue"),
    ).filter(
        Payment.status == PaymentStatus.SUCCESS,
        Payment.created_at >= thirty_days_ago,
    ).group_by(func.strftime("%Y-%m-%d", Payment.created_at))\
     .order_by(func.strftime("%Y-%m-%d", Payment.created_at))\
     .all()
    revenue_by_day = [{"date": r.day, "revenue_paise": int(r.revenue)} for r in revenue_by_day_rows]

    # ── New signups by day (last 30 days) ────────────────────────────────
    signups_by_day_rows = db.query(
        func.strftime("%Y-%m-%d", User.created_at).label("day"),
        func.count(User.id).label("count"),
    ).filter(User.created_at >= thirty_days_ago)\
     .group_by(func.strftime("%Y-%m-%d", User.created_at))\
     .order_by(func.strftime("%Y-%m-%d", User.created_at))\
     .all()
    signups_by_day = [{"date": r.day, "signups": r.count} for r in signups_by_day_rows]

    # ── Order status breakdown ────────────────────────────────────────────
    status_rows = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    order_status = {row[0].value if row[0] else "unknown": row[1] for row in status_rows}

    # ── Payment status breakdown ──────────────────────────────────────────
    pay_rows = db.query(Payment.status, func.count(Payment.id)).group_by(Payment.status).all()
    payment_status = {row[0].value if row[0] else "unknown": row[1] for row in pay_rows}

    # ── Top 10 vendors by order volume ───────────────────────────────────
    top_vendor_rows = db.query(
        Order.vendor_id,
        func.count(Order.id).label("order_count"),
        func.coalesce(func.sum(Order.total_amount), 0).label("total_revenue"),
    ).group_by(Order.vendor_id)\
     .order_by(func.count(Order.id).desc())\
     .limit(10).all()
    top_vendors = [
        {
            "vendor_id": r.vendor_id,
            "order_count": r.order_count,
            "total_revenue_paise": int(r.total_revenue),
        }
        for r in top_vendor_rows
    ]

    # ── Peak hours (all-time order distribution by hour) ──────────────────
    peak_rows = db.query(
        func.strftime("%H", Order.created_at).label("hour"),
        func.count(Order.id).label("count"),
    ).group_by(func.strftime("%H", Order.created_at))\
     .order_by(func.strftime("%H", Order.created_at))\
     .all()
    peak_hours = {int(r.hour): r.count for r in peak_rows}

    # ── Week-over-week comparison ─────────────────────────────────────────
    this_week_orders = db.query(func.count(Order.id)).filter(
        Order.created_at >= this_week_start
    ).scalar() or 0
    last_week_orders = db.query(func.count(Order.id)).filter(
        Order.created_at >= last_week_start,
        Order.created_at < this_week_start,
    ).scalar() or 0

    this_week_revenue = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == PaymentStatus.SUCCESS,
        Payment.created_at >= this_week_start,
    ).scalar() or 0
    last_week_revenue = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == PaymentStatus.SUCCESS,
        Payment.created_at >= last_week_start,
        Payment.created_at < this_week_start,
    ).scalar() or 0

    # ── Fraud statistics ──────────────────────────────────────────────────
    total_flagged = db.query(func.count(Order.id)).filter(Order.fraud_flag == True).scalar() or 0
    fraud_rate_pct = round(total_flagged / total_orders * 100, 2) if total_orders else 0.0

    return {
        "totals": {
            "users": total_users,
            "vendors": total_vendors,
            "students": total_students,
            "orders": total_orders,
            "revenue_paise": int(total_revenue_paise),
        },
        "orders_by_day": orders_by_day,
        "revenue_by_day": revenue_by_day,
        "signups_by_day": signups_by_day,
        "order_status": order_status,
        "payment_status": payment_status,
        "top_vendors": top_vendors,
        "peak_hours": peak_hours,
        "week_comparison": {
            "this_week": {"orders": this_week_orders, "revenue_paise": int(this_week_revenue)},
            "last_week": {"orders": last_week_orders, "revenue_paise": int(last_week_revenue)},
            "order_delta": this_week_orders - last_week_orders,
            "revenue_delta_paise": int(this_week_revenue) - int(last_week_revenue),
        },
        "fraud_stats": {
            "total_flagged": total_flagged,
            "fraud_rate_pct": fraud_rate_pct,
        },
    }


@router.get("/policies/faculty-priority")
def get_faculty_priority_policy_endpoint(user=Depends(require_role("admin"))) -> dict[str, Any]:
    return get_faculty_priority_policy()


@router.post("/policies/faculty-priority")
def set_faculty_priority_policy_endpoint(
    enabled: bool,
    start_hour: int = 12,
    end_hour: int = 14,
    user=Depends(require_role("admin")),
) -> dict[str, Any]:
    if start_hour < 0 or start_hour > 23 or end_hour < 1 or end_hour > 24:
        raise HTTPException(status_code=400, detail="Hours must be within 0-24")
    if end_hour <= start_hour:
        raise HTTPException(status_code=400, detail="end_hour must be greater than start_hour")

    return set_faculty_priority_policy(enabled, start_hour, end_hour)


@router.get("/policies/university")
def get_university_policy_endpoint(user=Depends(require_role("admin"))) -> dict[str, Any]:
    return get_university_policy()


@router.post("/policies/university")
def set_university_policy_endpoint(
    enabled: bool,
    break_start_hour: int = 12,
    break_end_hour: int = 14,
    max_orders_per_user: int = 3,
    min_slot_duration_minutes: int = 15,
    user=Depends(require_role("admin")),
) -> dict[str, Any]:
    if break_start_hour < 0 or break_start_hour > 23:
        raise HTTPException(status_code=400, detail="break_start_hour must be in 0-23")
    if break_end_hour < 1 or break_end_hour > 24:
        raise HTTPException(status_code=400, detail="break_end_hour must be in 1-24")
    if break_end_hour <= break_start_hour:
        raise HTTPException(status_code=400, detail="break_end_hour must be greater than break_start_hour")
    if max_orders_per_user < 1:
        raise HTTPException(status_code=400, detail="max_orders_per_user must be at least 1")
    if min_slot_duration_minutes < 5:
        raise HTTPException(status_code=400, detail="min_slot_duration_minutes must be at least 5")

    return set_university_policy(
        enabled=enabled,
        break_start_hour=break_start_hour,
        break_end_hour=break_end_hour,
        max_orders_per_user=max_orders_per_user,
        min_slot_duration_minutes=min_slot_duration_minutes,
    )


# 📢 GLOBAL ANNOUNCEMENT
@router.post("/announce")
def send_global_announcement(
    message: str,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
) -> dict[str, Any]:
    """Send notification to all users"""
    from app.modules.notifications.service import notify_user

    users = db.query(User).all()
    for user_obj in users:
        notify_user(
            user_id=user_obj.id,
            phone=user_obj.phone,
            title="Admin Announcement",
            message=message,
            db=db
        )

    return {"message": "Announcement sent to all users"}
