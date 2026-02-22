from datetime import timedelta, date

from sqlalchemy import func
from backend import models


def calculate_projection(db, item, forecast_days=7):
    """
    Calculates a day-by-day stock projection for the given item.
    Returns: List of dicts [{"date": date_obj, "projected_stock": int}]
    """
    today = date.today()
    projections = []
    
    current_stock = item.current_stock
    
    # Pre-fetch all relevant transactions once to avoid N+1 queries in the loop
    # In a real app we might optimize this further, but for a 7-day window this is fine.
    demand_orders = db.query(models.DemandOrder).filter(
        models.DemandOrder.item_id == item.id,
        models.DemandOrder.status == "OPEN"
    ).all()
    
    supply_orders = db.query(models.SupplyOrder).filter(
        models.SupplyOrder.item_id == item.id,
        models.SupplyOrder.status == "ORDERED"
    ).all()
    
    production_runs = db.query(models.ProductionRun).filter(
        models.ProductionRun.item_id == item.id,
        models.ProductionRun.status.in_(["PLANNED", "IN_PROGRESS"])
    ).all()

    running_stock = current_stock
    
    for i in range(forecast_days):
        target_date = today + timedelta(days=i)
        
        # Calculate changes for this specific day
        daily_demand = sum(o.quantity for o in demand_orders if o.due_date == target_date)
        daily_supply = sum(o.quantity for o in supply_orders if o.expected_delivery_date == target_date)
        daily_production = sum(o.quantity for o in production_runs if o.end_date == target_date)
        
        # We also need to account for past-due orders on Day 0 (Today)
        if i == 0:
            past_due_demand = sum(o.quantity for o in demand_orders if o.due_date < target_date)
            daily_demand += past_due_demand
            
            past_due_supply = sum(o.quantity for o in supply_orders if o.expected_delivery_date < target_date)
            daily_supply += past_due_supply
            
            past_due_production = sum(o.quantity for o in production_runs if o.end_date < target_date)
            daily_production += past_due_production

        running_stock = running_stock - daily_demand + daily_supply + daily_production
        
        projections.append({
            "day": i,
            "date": target_date,
            "projected_stock": running_stock,
            "demand": daily_demand,
            "supply": daily_supply + daily_production
        })

    return projections