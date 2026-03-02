from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderHistoryResponse(BaseModel):
    status: str
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)
