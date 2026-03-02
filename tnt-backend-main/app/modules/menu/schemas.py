from pydantic import BaseModel


class MenuItemCreate(BaseModel):
    name: str
    description: str | None = None
    price: int


class MenuItemResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: int
    image_url: str
    is_available: bool

    class Config:
        from_attributes = True