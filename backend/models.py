from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.database import Base


# -----------------------------
# ITEMS TABLE
# -----------------------------
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)

    cost_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)

    current_stock = Column(Integer, nullable=False)
    safety_stock = Column(Integer, default=0)
    min_order_qty = Column(Integer, default=1)

    demand_orders = relationship("DemandOrder", back_populates="item")
    supply_orders = relationship("SupplyOrder", back_populates="item")
    production_runs = relationship("ProductionRun", back_populates="item")
    alerts = relationship("Alert", back_populates="item")
    demands = relationship("Demand", back_populates="item")
    supplies = relationship("Supply", back_populates="item")
    
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import date


class Demand(Base):
    __tablename__ = "demands"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Integer, nullable=False)
    demand_date = Column(Date, default=date.today)

    item = relationship("Item", back_populates="demands")


class Supply(Base):
    __tablename__ = "supplies"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Integer, nullable=False)
    supply_date = Column(Date, default=date.today)

    item = relationship("Item", back_populates="supplies")




# -----------------------------
# SUPPLIERS TABLE
# -----------------------------
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact_email = Column(String, nullable=True)
    lead_time_days = Column(Integer, default=7)
    reliability_score = Column(Float, default=1.0)

    supply_orders = relationship("SupplyOrder", back_populates="supplier")


# -----------------------------
# DEMAND ORDERS TABLE
# -----------------------------
class DemandOrder(Base):
    __tablename__ = "demand_orders"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    customer_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    priority = Column(String, nullable=False)
    status = Column(String, default="OPEN")

    item = relationship("Item", back_populates="demand_orders")


# -----------------------------
# SUPPLY ORDERS TABLE
# -----------------------------
class SupplyOrder(Base):
    __tablename__ = "supply_orders"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    quantity = Column(Integer, nullable=False)
    order_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=False)
    status = Column(String, default="ORDERED")

    item = relationship("Item", back_populates="supply_orders")
    supplier = relationship("Supplier", back_populates="supply_orders")


# -----------------------------
# PRODUCTION RUNS TABLE
# -----------------------------
class ProductionRun(Base):
    __tablename__ = "production_runs"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, default="PLANNED")

    item = relationship("Item", back_populates="production_runs")


# -----------------------------
# ALERTS TABLE
# -----------------------------
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    type = Column(String, nullable=False)  # SHORTAGE / OVERSTOCK
    message = Column(Text, nullable=False)
    severity = Column(String, nullable=False)  # RED / YELLOW
    status = Column(String, default="ACTIVE")
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="alerts")

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    recommended_qty = Column(Integer)
    status = Column(String, default="PENDING")  # PENDING / APPROVED / REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item")

