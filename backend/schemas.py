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
    customer_name: str
    quantity: int
    due_date: date
    priority: str = "MEDIUM"


class DemandResponse(DemandCreate):
    id: int

    class Config:
        from_attributes = True

class SupplyCreate(BaseModel):
    item_id: int
    supplier_name: Optional[str] = None
    quantity: int
    order_date: date
    expected_delivery_date: date



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


# -------- ITEM UPDATE --------
class ItemUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    current_stock: Optional[int] = None
    safety_stock: Optional[int] = None
    min_order_qty: Optional[int] = None

# -------- DEMAND UPDATE --------
class DemandOrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    quantity: Optional[int] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None
    status: Optional[str] = None

# -------- SUPPLY UPDATE --------
class SupplyOrderUpdate(BaseModel):
    supplier_name: Optional[str] = None
    quantity: Optional[int] = None
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[str] = None

# -------- PRODUCTION RUN UPDATE --------
class ProductionRunUpdate(BaseModel):
    quantity: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None

# -------- PRODUCTION RUN CREATE --------
class ProductionRunCreate(BaseModel):
    item_id: int
    quantity: int
    start_date: date
    end_date: date

# -------- SIMULATION INPUT --------
class SimulationInput(BaseModel):
    additional_demand: int = 0      # Add/subtract units from daily demand
    additional_supply: int = 0      # Add units to daily supply (e.g. from other business)
    supply_delay_days: int = 0      # e.g. +2 days for all supply
