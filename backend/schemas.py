from pydantic import BaseModel
from typing import Optional
from datetime import date
from pydantic import BaseModel

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

class DemandCreate(BaseModel):
    item_id: int
    quantity: int
    demand_date: date


class DemandResponse(DemandCreate):
    id: int

    class Config:
        from_attributes = True

class SupplyCreate(BaseModel):
    item_id: int
    supplier_id: int   # ADD THIS
    quantity: int
    supply_date: date



class SupplyResponse(SupplyCreate):
    id: int

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: int
    item_id: int
    type: str
    message: str
    severity: str
    status: str
    resolution_note: Optional[str] = None

    class Config:
        from_attributes = True


# -------- SIMULATION INPUT --------
class SimulationInput(BaseModel):
    extra_demand: int = 0
    extra_supply: int = 0
