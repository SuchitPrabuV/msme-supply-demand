from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models
from backend.engine import calculate_projection
from backend.recommendation_engine import generate_recommendation
from backend.schemas import SimulationInput
from backend.alert_engine import run_alert_engine


router = APIRouter(prefix="/api", tags=["Projection"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- PROJECTION ----------------
@router.get("/projections/{item_id}")
def get_projection(item_id: int, db: Session = Depends(get_db)):

    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    projections = calculate_projection(db, item)

    # Run recommendation first to ensure email pulls fresh data
    recommendation = generate_recommendation(db, item, projections)

    # Run alert engine on the full time-series
    run_alert_engine(db, item, projections)

    return {
        "item": {
            "id": item.id,
            "sku": item.sku,
            "name": item.name,
            "current_stock": item.current_stock,
            "safety_stock": item.safety_stock,
        },
        "projections": projections,
        "summary": {
            "min_projected_stock": min(p["projected_stock"] for p in projections),
            "is_critical": any(p["projected_stock"] < item.safety_stock for p in projections)
        },
        "recommendation": recommendation
    }