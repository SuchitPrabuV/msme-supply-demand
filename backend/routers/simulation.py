from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models
from backend.engine import calculate_projection
from backend.schemas import SimulationInput

router = APIRouter(prefix="/api", tags=["Simulation"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/simulate/{item_id}")
def simulate_projection(
    item_id: int,
    simulation: SimulationInput,
    db: Session = Depends(get_db)
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Base projection (no overrides)
    base_projections = calculate_projection(db, item)

    # Simulated projection (with overrides applied)
    sim_projections = calculate_projection(
        db,
        item,
        sim_add_demand=simulation.additional_demand,
        sim_add_supply=simulation.additional_supply,
        sim_supply_delay=simulation.supply_delay_days
    )

    is_stockout_risk = any(p["projected_stock"] < item.safety_stock for p in sim_projections)

    return {
        "item": {
            "id": item.id,
            "sku": item.sku,
            "name": item.name,
            "current_stock": item.current_stock,
            "safety_stock": item.safety_stock,
        },
        "base_projections": base_projections,
        "simulated_projections": sim_projections,
        "summary": {
            "is_stockout_risk": is_stockout_risk,
        }
    }
