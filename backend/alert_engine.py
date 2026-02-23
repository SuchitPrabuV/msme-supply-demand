from backend import models
from datetime import datetime


def run_alert_engine(db, item, projections):
    """
    Scans the 7-day projection for stockout risks.
    projections: List of dicts from engine.calculate_projection
    """
    
    first_shortage_day = None
    first_warning_day = None

    for p in projections:
        stock = p["projected_stock"]
        
        # Rule: RED -> projected_stock < safety_stock
        if stock < item.safety_stock:
            if first_shortage_day is None:
                first_shortage_day = p["date"]
        
        # Rule: YELLOW -> projected_stock < 1.5 * safety_stock
        elif stock < (item.safety_stock * 1.5):
            if first_warning_day is None:
                first_warning_day = p["date"]

    existing_alert = db.query(models.Alert).filter(
        models.Alert.item_id == item.id,
        models.Alert.status == "ACTIVE"
    ).first()

    # Horizon Stock Logic
    horizon_stock = projections[-1]["projected_stock"] if projections else item.current_stock
    
    # Rule check for RED (Critical)
    is_red_needed = first_shortage_day is not None and horizon_stock < item.safety_stock
    
    # Rule check for YELLOW (Warning)
    is_yellow_needed = first_warning_day is not None and horizon_stock < (item.safety_stock * 1.5)
    
    if is_red_needed:
        severity = "RED"
        msg = f"CRITICAL [{item.sku} - {item.name}]: Stockout expected on {first_shortage_day.strftime('%d-%m-%Y')}"
        
        if not existing_alert:
            new_alert = models.Alert(
                item_id=item.id,
                type="SHORTAGE",
                message=msg,
                severity="RED",
                status="ACTIVE",
                created_at=datetime.utcnow()
            )
            db.add(new_alert)
        else:
            existing_alert.severity = "RED"
            existing_alert.message = msg
            existing_alert.status = "ACTIVE"
        db.commit()
    
    elif is_yellow_needed:
        severity = "YELLOW"
        msg = f"WARNING [{item.sku} - {item.name}]: Low stock risk around {first_warning_day.strftime('%d-%m-%Y')}"

        if not existing_alert:
            new_alert = models.Alert(
                item_id=item.id,
                type="SHORTAGE",
                message=msg,
                severity="YELLOW",
                status="ACTIVE",
                created_at=datetime.utcnow()
            )
            db.add(new_alert)
        else:
            existing_alert.severity = "YELLOW"
            existing_alert.message = msg
            existing_alert.status = "ACTIVE"
        db.commit()
            
    else:
        # Resolve any active alert if stock is healthy at the horizon
        if existing_alert:
            existing_alert.status = "RESOLVED"
            if horizon_stock >= (item.safety_stock * 1.5):
                existing_alert.resolution_note = f"Horizon stock ({horizon_stock}) is above warning threshold."
            else:
                existing_alert.resolution_note = "Stock levels are healthy."
            db.commit()
