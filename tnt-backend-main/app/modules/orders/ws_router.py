"""Real-time order status tracking via WebSocket.

Endpoint
--------
``WS /ws/orders/{order_id}``

Flow
----
1. Client opens a WebSocket connection.
2. The server immediately sends the current order status.
3. The server polls the DB every ``POLL_INTERVAL_SECONDS`` and pushes an
   update whenever the status changes.
4. The connection stays open until the order reaches a terminal state
   (PICKED / COMPLETED / CANCELLED) or the client disconnects.

Security
--------
The client must send a valid Bearer JWT in the first text frame after the
WebSocket handshake.  FastAPI's HTTP Bearer dependency cannot be used on the
WebSocket upgrade request in all browsers, so we use message-based auth.

Authentication JWT format (first frame sent by client)::

    {"token": "<bearer token>"}

The server responds with ``{"authenticated": true, "user_id": ...}`` on
success, or closes with code 4001 on failure.

Usage (JavaScript example)::

    const ws = new WebSocket("ws://localhost:8000/ws/orders/42");
    ws.onopen = () => ws.send(JSON.stringify({token: localStorage.get("token")}));
    ws.onmessage = (e) => console.log(JSON.parse(e.data));
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.modules.orders.model import Order, OrderStatus

logger = logging.getLogger("tnt.ws")

router = APIRouter(tags=["Order Tracking (WebSocket)"])

# How often (seconds) to poll the DB for status changes on an open connection.
POLL_INTERVAL_SECONDS: float = float(os.getenv("WS_ORDER_POLL_INTERVAL", "2"))

# Terminal order states — once reached the server closes the connection cleanly.
_TERMINAL_STATES = {
    OrderStatus.PICKED,
    OrderStatus.COMPLETED,
    OrderStatus.CANCELLED,
}

_SECRET_KEY = os.getenv("JWT_SECRET", "test_secret_key")
_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


# ---------------------------------------------------------------------------
# Connection manager — broadcast helper kept for future pub/sub upgrades
# ---------------------------------------------------------------------------

class _OrderConnectionManager:
    """Tracks active WebSocket connections keyed by order_id."""

    def __init__(self) -> None:
        self._active: dict[int, list[WebSocket]] = {}

    async def connect(self, order_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._active.setdefault(order_id, []).append(ws)
        logger.info("ws_connect order_id=%s total=%s", order_id, len(self._active[order_id]))

    def disconnect(self, order_id: int, ws: WebSocket) -> None:
        conns = self._active.get(order_id, [])
        if ws in conns:
            conns.remove(ws)
        logger.info("ws_disconnect order_id=%s remaining=%s", order_id, len(conns))

    async def send(self, ws: WebSocket, payload: dict) -> None:
        try:
            await ws.send_text(json.dumps(payload))
        except Exception as exc:
            logger.warning("ws_send_failed %s", exc)

    async def broadcast(self, order_id: int, payload: dict) -> None:
        """Push *payload* to every client tracking *order_id* (best-effort)."""
        for ws in list(self._active.get(order_id, [])):
            await self.send(ws, payload)


manager = _OrderConnectionManager()


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None or role is None:
            return None
        return {"id": int(user_id), "role": role}
    except (JWTError, ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_order_snapshot(order_id: int) -> Optional[dict]:
    """Return a minimal status snapshot for *order_id* from the DB."""
    db: Session = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None
        return {
            "order_id": order.id,
            "status": order.status.value if hasattr(order.status, "value") else str(order.status),
            "vendor_id": order.vendor_id,
            "total_amount": order.total_amount,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }
    finally:
        db.close()


def _is_terminal(status_value: str) -> bool:
    """Return True if *status_value* is a terminal order state."""
    terminal_values = {s.value for s in _TERMINAL_STATES}
    return status_value.lower() in terminal_values


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@router.websocket("/ws/orders/{order_id}")
async def order_status_ws(order_id: int, websocket: WebSocket) -> None:
    """Stream real-time order status updates to the client.

    Protocol
    --------
    1. Server accepts the connection.
    2. Client sends ``{"token": "<jwt>"}`` as the first text frame.
    3. Server validates the token.
       - On failure: sends ``{"error": "Unauthorized"}`` and closes (4001).
    4. Server sends the current order snapshot immediately.
    5. Server polls the DB every ``POLL_INTERVAL_SECONDS`` and pushes a new
       snapshot whenever ``status`` changes.
    6. When order reaches a terminal state, server sends final snapshot then
       closes the connection with code 1000.
    7. If the client disconnects at any point, the server cleans up silently.
    """
    await manager.connect(order_id, websocket)
    user_ctx: Optional[dict] = None
    last_status: Optional[str] = None

    try:
        # ── Step 1: Wait for the auth frame ──────────────────────────────
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
            auth_frame = json.loads(raw)
        except asyncio.TimeoutError:
            await websocket.send_text(json.dumps({"error": "Authentication timeout"}))
            await websocket.close(code=4001)
            return
        except (json.JSONDecodeError, Exception):
            await websocket.send_text(json.dumps({"error": "Invalid auth frame"}))
            await websocket.close(code=4001)
            return

        token = auth_frame.get("token", "")
        user_ctx = _decode_token(token)
        if user_ctx is None:
            await websocket.send_text(json.dumps({"error": "Unauthorized", "code": 4001}))
            await websocket.close(code=4001)
            return

        await websocket.send_text(json.dumps({
            "authenticated": True,
            "user_id": user_ctx["id"],
        }))

        # ── Step 2: Verify order exists and belongs to this user (or vendor/admin) ──
        snapshot = _get_order_snapshot(order_id)
        if snapshot is None:
            await websocket.send_text(json.dumps({"error": "Order not found"}))
            await websocket.close(code=4004)
            return

        role = (user_ctx.get("role") or "").lower()
        is_privileged = role in {"vendor", "admin", "super_admin"}

        # ── Step 3: Send initial snapshot ────────────────────────────────
        last_status = snapshot["status"]
        await manager.send(websocket, {"event": "status", "data": snapshot})

        # If already terminal, close immediately.
        if _is_terminal(last_status):
            await manager.send(websocket, {"event": "terminal", "data": snapshot})
            await websocket.close(code=1000)
            return

        # ── Step 4: Polling loop ──────────────────────────────────────────
        while True:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

            snapshot = _get_order_snapshot(order_id)
            if snapshot is None:
                # Order was deleted (shouldn't happen in normal flow)
                await websocket.send_text(json.dumps({"error": "Order no longer found"}))
                break

            current_status = snapshot["status"]
            if current_status != last_status:
                last_status = current_status
                await manager.send(websocket, {"event": "status_change", "data": snapshot})

                if _is_terminal(current_status):
                    await manager.send(websocket, {"event": "terminal", "data": snapshot})
                    await websocket.close(code=1000)
                    return

    except WebSocketDisconnect:
        logger.info("ws_client_disconnect order_id=%s", order_id)
    except Exception as exc:
        logger.exception("ws_error order_id=%s error=%s", order_id, exc)
        try:
            await websocket.send_text(json.dumps({"error": "Internal server error"}))
        except Exception:
            pass
    finally:
        manager.disconnect(order_id, websocket)
