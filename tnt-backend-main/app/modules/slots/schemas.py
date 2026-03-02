from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class SlotStatus(str, Enum):
    available = "available"
    limited = "limited"
    full = "full"

class SlotCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    max_orders: int

class SlotResponse(BaseModel):
    id: int
    vendor_id: int
    start_time: datetime
    end_time: datetime
    max_orders: int
    current_orders: int
    status: SlotStatus
    load_label: str = "LOW"
    express_pickup_eligible: bool = False

    model_config = ConfigDict(from_attributes=True)
