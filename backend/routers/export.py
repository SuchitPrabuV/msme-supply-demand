from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd
import io
from backend.database import SessionLocal
from backend import models

router = APIRouter(prefix="/api/export", tags=["Export"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/items")
def export_items(db: Session = Depends(get_db)):
    items = db.query(models.Item).all()
    data = []
    for i in items:
        data.append({
            "SKU": i.sku,
            "Name": i.name,
            "Category": i.category,
            "Current Stock": i.current_stock,
            "Safety Stock": i.safety_stock,
            "Cost Price": i.cost_price,
            "Selling Price": i.selling_price,
            "Min Order Qty": i.min_order_qty
        })
    
    df = pd.DataFrame(data)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=items_export.csv"
    return response

@router.get("/demand")
def export_demand(db: Session = Depends(get_db)):
    orders = db.query(models.DemandOrder).all()
    data = []
    for o in orders:
        data.append({
            "SKU": o.item.sku if o.item else "N/A",
            "Customer": o.customer_name,
            "Quantity": o.quantity,
            "Due Date": o.due_date,
            "Priority": o.priority,
            "Status": o.status
        })
    
    df = pd.DataFrame(data)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=demand_orders_export.csv"
    return response

@router.get("/supply")
def export_supply(db: Session = Depends(get_db)):
    orders = db.query(models.SupplyOrder).all()
    data = []
    for o in orders:
        data.append({
            "SKU": o.item.sku if o.item else "N/A",
            "Supplier": o.supplier_name,
            "Quantity": o.quantity,
            "Order Date": o.order_date,
            "Expected Delivery": o.expected_delivery_date,
            "Status": o.status
        })
    
    df = pd.DataFrame(data)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=supply_orders_export.csv"
    return response
