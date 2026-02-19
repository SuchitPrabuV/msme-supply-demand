from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import SessionLocal
from backend import models, schemas
from backend.models import Item
from backend.schemas import ItemResponse

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
@router.get("/", response_model=List[ItemResponse])
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
