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

    # Get baseline projections
    base_projections = calculate_projection(db, item)
    
    simulated_projections = []
    current_sim_stock = item.current_stock
    
    # We re-calculate the simulation step-by-step applying the extra demand/supply
    for p in base_projections:
        # Base daily changes
        daily_demand = p["demand"] + (simulation.extra_demand if p["day"] == 0 else 0) 
        # Note: extra_demand/supply can be interpreted as 'one-time' or 'ongoing'.
        # Usually 'What-If' for MSMEs is "What if this order comes in today?" or "What if everything increases?".
        # Let's assume extra_demand/supply are daily additions for simplicity in this demo or scale it.
        # Design Doc says "Allow user to scale Demand by +/- %".
        
        daily_supply = p["supply"] + (simulation.extra_supply if p["day"] == 0 else 0)

        current_sim_stock = current_sim_stock - daily_demand + daily_supply
        
        simulated_projections.append({
            "day": p["day"],
            "date": p["date"],
            "base_stock": p["projected_stock"],
            "simulated_stock": current_sim_stock
        })

    return {
        "item_name": item.name,
        "base_stock": item.current_stock,
        "simulation": simulated_projections
    }
