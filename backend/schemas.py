from pydantic import BaseModel
from typing import Optional


# -------- ITEM CREATE --------
class ItemCreate(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    cost_price: float
    selling_price: float
    current_stock: int
    safety_stock: int = 0
    min_order_qty: int = 1


# -------- ITEM RESPONSE --------
class ItemResponse(ItemCreate):
    id: int

    class Config:
        from_attributes = True
