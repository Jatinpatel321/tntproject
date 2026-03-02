from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class OrderStatus(str, Enum):
    # Canonical states (PROMPT 11)
    placed    = "placed"
    confirmed = "confirmed"
    ready     = "ready"
    picked    = "picked"
    cancelled = "cancelled"
    # Legacy states — kept for backward-compat with existing DB rows
    pending          = "pending"
    ready_for_pickup = "ready_for_pickup"
    completed        = "completed"


class OrderResponse(BaseModel):
    id: int
    slot_id: int
    vendor_id: int
    status: OrderStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
