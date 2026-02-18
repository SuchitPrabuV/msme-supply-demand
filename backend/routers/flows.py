from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import SessionLocal
from backend import models, schemas

router = APIRouter(prefix="/flows", tags=["Demand & Supply"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- DEMAND ---------------- #

@router.post("/demands/", response_model=schemas.DemandResponse)
def create_demand(demand: schemas.DemandCreate, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == demand.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db_demand = models.Demand(**demand.dict())
    db.add(db_demand)
    db.commit()
    db.refresh(db_demand)

    return db_demand


@router.get("/demands/{item_id}", response_model=List[schemas.DemandResponse])
def get_demands(item_id: int, db: Session = Depends(get_db)):
    return db.query(models.Demand).filter(models.Demand.item_id == item_id).all()


# ---------------- SUPPLY ---------------- #

@router.post("/supplies/", response_model=schemas.SupplyResponse)
def create_supply(supply: schemas.SupplyCreate, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == supply.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db_supply = models.Supply(**supply.dict())
    db.add(db_supply)
    db.commit()
    db.refresh(db_supply)

    return db_supply


@router.get("/supplies/{item_id}", response_model=List[schemas.SupplyResponse])
def get_supplies(item_id: int, db: Session = Depends(get_db)):
    return db.query(models.Supply).filter(models.Supply.item_id == item_id).all()
