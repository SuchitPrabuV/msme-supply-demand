from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from backend.database import SessionLocal
from backend import models, schemas
from backend.utils import refresh_item_status

router = APIRouter(prefix="/api/orders", tags=["Orders"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- DEMAND ORDERS ---

@router.get("/demand", response_model=List[schemas.DemandResponse])
def get_demand_orders(db: Session = Depends(get_db)):
    return db.query(models.DemandOrder).options(joinedload(models.DemandOrder.item)).all()

@router.post("/demand")
def create_demand_order(order: schemas.DemandCreate, db: Session = Depends(get_db)):
    db_order = models.DemandOrder(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Refresh item status
    refresh_item_status(db, db_order.item)
    
    return db_order

@router.put("/demand/{order_id}")
def update_demand_order(order_id: int, order_update: schemas.DemandOrderUpdate, db: Session = Depends(get_db)):
    db_order = db.query(models.DemandOrder).filter(models.DemandOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Demand Order not found")
    
    update_data = order_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_order, key, value)
    
    db.commit()
    db.refresh(db_order)
    
    # Refresh item status
    refresh_item_status(db, db_order.item)
    
    return db_order

@router.delete("/demand/{order_id}")
def delete_demand_order(order_id: int, db: Session = Depends(get_db)):
    db_order = db.query(models.DemandOrder).filter(models.DemandOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Demand Order not found")
    
    item = db_order.item
    db.delete(db_order)
    db.commit()
    
    # Refresh item status
    if item:
        refresh_item_status(db, item)
        
    return {"message": "Demand Order deleted successfully"}

@router.post("/demand/{order_id}/approve")
def approve_demand_order(order_id: int, db: Session = Depends(get_db)):
    db_order = db.query(models.DemandOrder).filter(models.DemandOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Demand Order not found")
    
    if db_order.status != "OPEN":
        raise HTTPException(status_code=400, detail="Only OPEN demand orders can be approved")
    
    item = db_order.item
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.current_stock < db_order.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock ({item.current_stock}) to approve order ({db_order.quantity})")
    
    # Process approval
    item.current_stock -= db_order.quantity
    db_order.status = "APPROVED"
    
    db.commit()
    
    # Refresh item status
    refresh_item_status(db, item)
    
    return {"message": "Demand order approved and inventory deducted"}

# --- SUPPLY ORDERS ---

@router.get("/supply")
def get_supply_orders(db: Session = Depends(get_db)):
    return db.query(models.SupplyOrder).options(
        joinedload(models.SupplyOrder.item)
    ).all()

@router.post("/supply")
def create_supply_order(order: schemas.SupplyCreate, db: Session = Depends(get_db)):
    db_order = models.SupplyOrder(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Refresh item status
    refresh_item_status(db, db_order.item)
    
    return db_order

@router.put("/supply/{order_id}")
def update_supply_order(order_id: int, order_update: schemas.SupplyOrderUpdate, db: Session = Depends(get_db)):
    db_order = db.query(models.SupplyOrder).filter(models.SupplyOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Supply Order not found")
    
    update_data = order_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_order, key, value)
    
    db.commit()
    db.refresh(db_order)
    
    # Refresh item status
    refresh_item_status(db, db_order.item)
    
    return db_order

@router.get("/supply/nearing", response_model=List[schemas.SupplyResponse])
def get_nearing_supply_orders(db: Session = Depends(get_db)):
    from datetime import date, timedelta
    today = date.today()
    in_three_days = today + timedelta(days=3)
    
    # Orders arriving within 3 days that haven't been followed up and aren't already RECEIVED
    return db.query(models.SupplyOrder).options(joinedload(models.SupplyOrder.item)).filter(
        models.SupplyOrder.expected_delivery_date <= in_three_days,
        models.SupplyOrder.expected_delivery_date >= today,
        models.SupplyOrder.followed_up == False,
        models.SupplyOrder.status != "RECEIVED"
    ).all()

@router.post("/supply/{order_id}/followup")
def acknowledge_followup(order_id: int, db: Session = Depends(get_db)):
    db_order = db.query(models.SupplyOrder).filter(models.SupplyOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Supply Order not found")
    
    db_order.followed_up = True
    db.commit()
    return {"message": "Follow-up acknowledged"}

@router.delete("/supply/{order_id}")
def delete_supply_order(order_id: int, db: Session = Depends(get_db)):
    db_order = db.query(models.SupplyOrder).filter(models.SupplyOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Supply Order not found")
    
    item = db_order.item
    db.delete(db_order)
    db.commit()
    
    # Refresh item status
    if item:
        refresh_item_status(db, item)
        
    return {"message": "Supply Order deleted successfully"}
