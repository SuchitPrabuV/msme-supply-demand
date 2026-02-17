from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend import models, schemas

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
