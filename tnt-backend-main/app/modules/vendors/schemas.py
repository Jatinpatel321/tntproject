from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VendorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    description: str
    vendor_type: str
    is_approved: bool
    phone: str
    is_open: bool
    logo_url: str | None = None
    live_load_label: str
    express_pickup_eligible: bool


class VendorMenuItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vendor_id: int
    name: str
    description: str | None
    price: int
    image_url: str
    is_available: bool


class VendorSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vendor_id: int
    start_time: datetime
    end_time: datetime
    is_available: bool
    max_orders: int
    current_orders: int
    load_label: str
    express_pickup_eligible: bool
