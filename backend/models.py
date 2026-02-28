from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, date
from backend.database import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    contact_email = Column(String, nullable=True)
    lead_time_days = Column(Integer, default=7)
    reliability_score = Column(Float, default=1.0)

    # Relationships
    items = relationship("Item", back_populates="supplier")


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
    overstock_multiplier = Column(Integer, default=3)
    lead_time = Column(Integer, default=7)
    warning_multiplier = Column(Float, default=1.5)
    reorder_target_multiplier = Column(Float, default=3.0)

    # Capacity fields (PS requirements)
    machine_capacity = Column(Float, default=100.0) # units per day
    shift_capacity = Column(Float, default=8.0) # hours per shift

    # Supplier Link
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="items")
    demand_orders = relationship("DemandOrder", back_populates="item", cascade="all, delete-orphan")
    supply_orders = relationship("SupplyOrder", back_populates="item", cascade="all, delete-orphan")
    production_runs = relationship("ProductionRun", back_populates="item", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="item", cascade="all, delete-orphan")
    demands = relationship("Demand", back_populates="item", cascade="all, delete-orphan")
    supplies = relationship("Supply", back_populates="item", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="item", cascade="all, delete-orphan")


class Demand(Base):
    __tablename__ = "demands"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    demand_date = Column(Date, default=date.today)

    item = relationship("Item", back_populates="demands")


class Supply(Base):
    __tablename__ = "supplies"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    supply_date = Column(Date, default=date.today)

    item = relationship("Item", back_populates="supplies")


class DemandOrder(Base):
    __tablename__ = "demand_orders"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    customer_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    priority = Column(String, nullable=False)
    status = Column(String, default="OPEN")

    item = relationship("Item", back_populates="demand_orders")


class SupplyOrder(Base):
    __tablename__ = "supply_orders"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    supplier_name = Column(String, nullable=True)
    quantity = Column(Integer, nullable=False)
    order_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=False)
    status = Column(String, default="DRAFT")
    followed_up = Column(Boolean, default=False)

    item = relationship("Item", back_populates="supply_orders")
    supplier = relationship("Supplier")


class ProductionRun(Base):
    __tablename__ = "production_runs"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, default="PLANNED")

    item = relationship("Item", back_populates="production_runs")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)  # SHORTAGE / OVERSTOCK
    message = Column(Text, nullable=False)
    severity = Column(String, nullable=False)  # RED / YELLOW
    status = Column(String, default="ACTIVE")
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="alerts")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    recommended_qty = Column(Integer)
    rationale = Column(Text, nullable=True)
    status = Column(String, default="PENDING")  # PENDING / APPROVED / REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="recommendations")

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    sender_email = Column(String, nullable=True)
    app_password = Column(String, nullable=True)
    recipient_email = Column(String, nullable=True)
    alerts_enabled = Column(Boolean, default=True)
