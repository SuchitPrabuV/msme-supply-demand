from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models

router = APIRouter(prefix="/api", tags=["Simulation"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/simulate/{item_id}")
def simulate_projection(
    item_id: int,
    demand_multiplier: float = 1.0,
    db: Session = Depends(get_db)
):

    item = db.query(models.Item).filter(
        models.Item.id == item_id
    ).first()

    if not item:
        return {"error": "Item not found"}

    simulated_stock = item.current_stock
    simulated_projection = []

    for day in range(7):

        simulated_demand = int(0 * demand_multiplier)  # adjust if demand exists
        simulated_supply = 0

        simulated_stock = simulated_stock - simulated_demand + simulated_supply

        simulated_projection.append({
            "day": day + 1,
            "projected_stock": simulated_stock
        })

    return {
        "item_name": item.name,
        "simulation": simulated_projection
    }
