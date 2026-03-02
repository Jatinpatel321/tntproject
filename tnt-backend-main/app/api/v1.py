"""API v1 aggregator.

All domain routers are collected here under the ``/v1`` prefix so that
*every* endpoint is available at both:

  • /v1/<domain>/...    ← canonical, going-forward address
  • /<domain>/...       ← legacy address (kept for backward-compat while
                           the frontend migrates; removed in v2)

Adding a new domain router
--------------------------
Import it and call ``api_v1_router.include_router(...)`` — the versioned
prefix is handled automatically.  No changes to ``app/main.py`` needed for
the v1 family.

Deprecation timeline
--------------------
Legacy (un-prefixed) routes will be removed once the frontend has migrated.
The ``deprecated=True`` flag on the legacy includes in ``app/main.py``
surfaces this in the OpenAPI docs.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.admin.router import router as admin_router
from app.modules.ai_intelligence.router import router as ai_router
from app.modules.auth.router import router as auth_router
from app.modules.cart.router import router as cart_router
from app.modules.complaints.router import router as complaints_router
from app.modules.feedback.router import router as feedback_router
from app.modules.group_cart.router import router as group_cart_router
from app.modules.ledger.router import router as ledger_router
from app.modules.menu.router import router as menu_router
from app.modules.notifications.router import router as notification_router
from app.modules.orders.router import router as orders_router
from app.modules.payments.router import router as payments_router
from app.modules.payments.webhook import router as razorpay_webhook_router
from app.modules.rewards.router import router as rewards_router
from app.modules.slots.router import router as slots_router
from app.modules.stationery.payment_router import router as stationery_payment_router
from app.modules.stationery.router import router as stationery_router
from app.modules.users.router import router as users_router
from app.modules.vendors.router import router as vendors_router
from app.modules.orders.ws_router import router as orders_ws_router

api_v1_router = APIRouter(prefix="/v1")

# ── Domain routers ────────────────────────────────────────────────────────
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(slots_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(payments_router)
api_v1_router.include_router(razorpay_webhook_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(stationery_router)
api_v1_router.include_router(stationery_payment_router)
api_v1_router.include_router(notification_router)
api_v1_router.include_router(rewards_router)
api_v1_router.include_router(group_cart_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(menu_router)
api_v1_router.include_router(vendors_router)
api_v1_router.include_router(ledger_router)
api_v1_router.include_router(feedback_router)
api_v1_router.include_router(complaints_router)
api_v1_router.include_router(cart_router)
# WebSocket routes are also available under /v1 for clients using the versioned base URL
api_v1_router.include_router(orders_ws_router)
