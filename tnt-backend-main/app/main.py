from contextlib import asynccontextmanager
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.emergency import is_emergency_shutdown_enabled
from app.core.logging_setup import configure_logging
from app.core.observability import observability
from app.core.rate_limit_middleware import RateLimitMiddleware
from app.core.redis import redis_client
from app.core.startup_checks import validate_production_settings, verify_database_revision
from app.database.init_db import init_db
from app.database.session import engine
from app.api.v1 import api_v1_router
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.LOG_JSON)
    validate_production_settings(settings.APP_ENV, settings.CORS_ORIGINS)
    init_db()
    if settings.DB_REVISION_GUARD:
        verify_database_revision()
    yield


app = FastAPI(title="TNT – Tap N Take", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Rate-limiting middleware — protects /payments/* and /stationery/payments/*
# by IP address.  Auth route limits are handled via route-level dependencies
# in app/modules/auth/router.py.
app.add_middleware(RateLimitMiddleware)

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SHUTDOWN_GUARDED_PREFIXES = (
    # legacy (un-prefixed) paths
    "/cart",
    "/orders",
    "/payments",
    "/stationery",
    "/groups",
    # v1 paths
    "/v1/cart",
    "/v1/orders",
    "/v1/payments",
    "/v1/stationery",
    "/v1/groups",
)
SHUTDOWN_EXEMPT_PATHS = {
    "/admin/shutdown",
    "/v1/admin/shutdown",
}


@app.middleware("http")
async def emergency_shutdown_gate(request: Request, call_next):
    path = request.url.path
    if request.method in MUTATING_METHODS:
        if path not in SHUTDOWN_EXEMPT_PATHS and path.startswith(SHUTDOWN_GUARDED_PREFIXES):
            if is_emergency_shutdown_enabled():
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": "Service temporarily unavailable due to emergency shutdown",
                        "emergency_shutdown": True,
                    },
                )

    return await call_next(request)


@app.middleware("http")
async def capture_metrics(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await observability.track_request(request, call_next)
    if settings.ENABLE_METRICS:
        observability.maybe_alert_error_budget(
            threshold_percent=settings.ERROR_BUDGET_PERCENT,
            min_requests=settings.ERROR_BUDGET_MIN_REQUESTS,
            alert_webhook_url=settings.ALERT_WEBHOOK_URL,
        )

    response.headers["x-request-id"] = request_id
    return response


@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def readiness() -> JSONResponse:
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")

        if settings.DB_REVISION_GUARD:
            verify_database_revision()

        return JSONResponse(status_code=200, content={"status": "ready"})
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "not_ready", "detail": str(exc)})


@app.get("/health/deep")
def deep_readiness() -> JSONResponse:
    checks = {
        "database": "fail",
        "redis": "fail",
        "migrations": "skip" if not settings.DB_REVISION_GUARD else "fail",
    }

    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        checks["database"] = "ok"

        redis_client.ping()
        checks["redis"] = "ok"

        if settings.DB_REVISION_GUARD:
            verify_database_revision()
            checks["migrations"] = "ok"

        return JSONResponse(status_code=200, content={"status": "ready", "checks": checks})
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "checks": checks, "detail": str(exc)},
        )


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    snapshot = observability.snapshot()
    snapshot["error_budget_percent_threshold"] = settings.ERROR_BUDGET_PERCENT
    snapshot["error_budget_min_requests"] = settings.ERROR_BUDGET_MIN_REQUESTS
    return snapshot

# ── v1 (canonical, going-forward) ────────────────────────────────────────
# All domain routers live under /v1/<domain>/... via the aggregator.
app.include_router(api_v1_router)

# ── Legacy (un-prefixed) routes — DEPRECATED, kept for backward-compat ───
# These will be removed once the frontend has migrated to /v1.
# ``deprecated=True`` in include_router surfaces a deprecation notice in the
# OpenAPI docs for each legacy route.
app.include_router(auth_router, deprecated=True)
app.include_router(users_router, deprecated=True)
app.include_router(slots_router, deprecated=True)
app.include_router(orders_router, deprecated=True)
app.include_router(payments_router, deprecated=True)
app.include_router(razorpay_webhook_router, deprecated=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(admin_router, deprecated=True)
app.include_router(stationery_router, deprecated=True)
app.include_router(stationery_payment_router, deprecated=True)
app.include_router(notification_router, deprecated=True)
app.include_router(rewards_router, deprecated=True)
app.include_router(group_cart_router, deprecated=True)
app.include_router(ai_router, deprecated=True)
app.include_router(menu_router, deprecated=True)
app.include_router(vendors_router, deprecated=True)
app.include_router(ledger_router, deprecated=True)
app.include_router(feedback_router, deprecated=True)
app.include_router(complaints_router, deprecated=True)
app.include_router(cart_router, deprecated=True)

# 🔌 WebSocket — real-time order tracking (not versioned; protocol-level upgrade)
app.include_router(orders_ws_router)
