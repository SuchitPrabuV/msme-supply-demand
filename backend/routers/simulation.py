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

    # Calculate status for both
    def get_alert_status(projections):
        first_shortage_day = None
        for p in projections:
            if p["projected_stock"] < item.safety_stock:
                if first_shortage_day is None:
                    first_shortage_day = p["date"]
        
        horizon_stock = projections[-1]["projected_stock"] if projections else item.current_stock
        is_red = first_shortage_day is not None and horizon_stock < item.safety_stock
        is_warning = (
            not is_red 
            and horizon_stock < (item.safety_stock * item.warning_multiplier)
            and horizon_stock < item.current_stock
        )
        is_overstock = (
            horizon_stock > (item.safety_stock * item.overstock_multiplier) 
            and item.current_stock >= item.safety_stock 
            and item.safety_stock > 0
        )
        
        return {
            "is_critical": is_red,
            "is_warning": is_warning,
            "is_overstock": is_overstock,
            "shortage_date": first_shortage_day.strftime('%d-%m-%Y') if first_shortage_day else None,
            "horizon_stock": int(horizon_stock)
        }

    base_status = get_alert_status(base_projections)
    sim_status = get_alert_status(sim_projections)

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
            "base": base_status,
            "sim": sim_status,
            "is_stockout_risk": sim_status["is_critical"]  # Keep for backward compatibility if needed
        }
    }
