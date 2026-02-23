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
