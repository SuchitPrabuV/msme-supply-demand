from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, date
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

    # Relationships
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
    supplier_name = Column(String, nullable=True)
    quantity = Column(Integer, nullable=False)
    order_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=False)
    status = Column(String, default="ORDERED")

    item = relationship("Item", back_populates="supply_orders")


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
    status = Column(String, default="PENDING")  # PENDING / APPROVED / REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="recommendations")
