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

    demands = db.query(models.Demand).filter(
        models.Demand.item_id == item_id
    ).all()

    supplies = db.query(models.Supply).filter(
        models.Supply.item_id == item_id
    ).all()

    projection = calculate_projection(item, demands, supplies)

    # Run alert engine (optional if already running in ingestion)
    #run_alert_engine(db, item, projection)

    from backend.recommendation_engine import generate_recommendation

    recommendation = generate_recommendation(db, item, projection)


    # Build daily view
    demand_by_date = {}
    for demand in demands:
        key = demand.demand_date.isoformat()
        demand_by_date[key] = demand_by_date.get(key, 0) + demand.quantity

    supply_by_date = {}
    for supply in supplies:
        key = supply.supply_date.isoformat()
        supply_by_date[key] = supply_by_date.get(key, 0) + supply.quantity

    projections = []
    for day in projection:
        day_key = day["date"]
        projections.append(
            {
                "date": day_key,
                "demand": demand_by_date.get(day_key, 0),
                "supply": supply_by_date.get(day_key, 0),
                "projected_stock": day["projected_stock"],
            }
        )

    return {
        "item": {
            "id": item.id,
            "sku": item.sku,
            "name": item.name,
            "current_stock": item.current_stock,
            "safety_stock": item.safety_stock,
        },
        "projections": projections,
        "recommendation": recommendation
    }


# ---------------- SIMULATION ----------------
@router.post("/simulate/{item_id}")
def simulate_projection(
    item_id: int,
    simulation: SimulationInput,
    db: Session = Depends(get_db)
):

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

    simulated_projection = []

    for day in projection:
        simulated_stock = (
            day["projected_stock"]
            - simulation.extra_demand
            + simulation.extra_supply
        )

        simulated_projection.append({
            "date": day["date"],
            "original_stock": day["projected_stock"],
            "simulated_stock": simulated_stock
        })

    return {
        "item_id": item_id,
        "simulation": simulated_projection
    }
