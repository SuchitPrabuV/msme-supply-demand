from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models
from backend.engine import calculate_projection

router = APIRouter(prefix="/api", tags=["Projection"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/projections/{item_id}")
def get_projection(item_id: int, db: Session = Depends(get_db)):

    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    demands = db.query(models.Demand).filter(
        models.Demand.item_id == item_id
    ).all()

    supplies = db.query(models.Supply).filter(
        models.Supply.item_id == item_id
    ).all()

    projection = calculate_projection(item, demands, supplies)

    return {
        "item_id": item_id,
        "current_stock": item.current_stock,
        "timeline": projection
    }
