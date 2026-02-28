from pydantic import BaseModel
from typing import Optional
from datetime import date
from pydantic import BaseModel

# -------- SUPPLIER SCHEMAS --------
class SupplierBase(BaseModel):
    name: str
    contact_email: Optional[str] = None
    lead_time_days: int = 7
    reliability_score: float = 1.0

class SupplierCreate(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: int

    class Config:
        from_attributes = True

# -------- ITEM CREATE --------
class ItemCreate(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    cost_price: float = 0.0
    selling_price: float = 0.0
    current_stock: int
    safety_stock: int = 0
    min_order_qty: int = 1
    overstock_multiplier: int = 3
    lead_time: int = 7
    warning_multiplier: float = 1.5
    reorder_target_multiplier: float = 2.0
    supplier_id: Optional[int] = None


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
    priority: Optional[str] = "MEDIUM"


class DemandResponse(DemandCreate):
    id: int
    status: str
    item: Optional[ItemResponse] = None

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
    followed_up: bool
    item: Optional[ItemResponse] = None

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
    overstock_multiplier: Optional[int] = None
    lead_time: Optional[int] = None
    warning_multiplier: Optional[float] = None
    reorder_target_multiplier: Optional[float] = None
    supplier_id: Optional[int] = None

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
    followed_up: Optional[bool] = None

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
# -------- SETTINGS --------
class SettingsBase(BaseModel):
    sender_email: Optional[str] = None
    app_password: Optional[str] = None
    recipient_email: Optional[str] = None
    alerts_enabled: bool = True

class SettingsResponse(SettingsBase):
    id: int

    class Config:
        from_attributes = True
