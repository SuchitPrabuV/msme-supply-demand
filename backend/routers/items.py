from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import SessionLocal
from backend import models, schemas
from backend.utils import refresh_item_status

router = APIRouter(prefix="/items", tags=["Items"])


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# CREATE ITEM
@router.post("/", response_model=schemas.ItemResponse)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):

    existing_item = db.query(models.Item).filter(models.Item.sku == item.sku).first()
    if existing_item:
        raise HTTPException(status_code=400, detail="Item with this SKU already exists")

    db_item = models.Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


# GET ALL ITEMS  ✅ (OUTSIDE CREATE FUNCTION)
@router.get("/", response_model=List[schemas.ItemResponse])
def get_items(db: Session = Depends(get_db)):
    items = db.query(models.Item).all()
    return items

@router.get("/{item_id}/update-stock")
def update_stock(
    item_id: int,
    current_stock: int,
    safety_stock: int,
    db: Session = Depends(get_db)
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.current_stock = current_stock
    item.safety_stock = safety_stock
    db.commit()

    return {"message": "Stock updated successfully"}


# UPDATE ITEM
@router.put("/{item_id}", response_model=schemas.ItemResponse)
def update_item(item_id: int, item_update: schemas.ItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)

    # Refresh alerts/recommendations using central utility
    refresh_item_status(db, db_item)

    return db_item


# DELETE ITEM
@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted successfully"}
