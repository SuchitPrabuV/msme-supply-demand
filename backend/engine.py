from datetime import timedelta, date

from sqlalchemy import func
from backend import models


def calculate_projection(db, item, forecast_days=14, sim_add_demand=0, sim_add_supply=0, sim_supply_delay=0):
    """
    Calculates a day-by-day stock projection for the given item.
    Supports simulation parameters without modifying the DB.
    """
    today = date.today()
    projections = []
    
    current_stock = item.current_stock
    
    # Pre-fetch all relevant transactions
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
        
        # Original dates for matching
        # If simulation delay is active, supply that originally arrived on Day X 
        # now arrives on Day X + delay.
        # Logic: We find supply whose (expected_date + delay) == target_date
        
        daily_demand = sum(o.quantity for o in demand_orders if o.due_date == target_date)
        
        # Apply Simulation Overrides: Add units directly
        daily_demand += sim_add_demand
        
        # Supply / Production matching with delay injection
        daily_supply = sum(o.quantity for o in supply_orders if (o.expected_delivery_date + timedelta(days=sim_supply_delay)) == target_date)
        daily_production = sum(o.quantity for o in production_runs if (o.end_date + timedelta(days=sim_supply_delay)) == target_date)
        
        # Apply Simulation Overrides: Add units directly
        daily_supply += sim_add_supply

        # Past-due handling on Day 0
        if i == 0:
            past_due_demand = sum(o.quantity for o in demand_orders if o.due_date < target_date)
            daily_demand += past_due_demand # Sim additive is already applied once to 'daily_demand' for today
            
            past_due_supply = sum(o.quantity for o in supply_orders if (o.expected_delivery_date + timedelta(days=sim_supply_delay)) < target_date)
            daily_supply += past_due_supply
            
            past_due_production = sum(o.quantity for o in production_runs if (o.end_date + timedelta(days=sim_supply_delay)) < target_date)
            daily_production += past_due_production

        running_stock = running_stock - daily_demand + daily_supply + daily_production
        
        projections.append({
            "day": i,
            "date": target_date,
            "projected_stock": round(running_stock, 2), # Handle float math from multiplier
            "demand": round(daily_demand, 2),
            "supply": round(daily_supply + daily_production, 2)
        })

    return projections
