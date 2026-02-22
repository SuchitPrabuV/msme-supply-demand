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
        if stock < item.safety_stock:
            if first_shortage_day is None:
                first_shortage_day = p["date"]
        elif stock < item.safety_stock * 1.5:
            if first_warning_day is None:
                first_warning_day = p["date"]

    existing_alert = db.query(models.Alert).filter(
        models.Alert.item_id == item.id,
        models.Alert.status == "ACTIVE"
    ).first()

    if first_shortage_day:
        severity = "RED"
        msg = f"CRITICAL: Stockout expected on {first_shortage_day.strftime('%d-%m-%Y')}"
        
        if not existing_alert or existing_alert.severity != "RED":
            # Resolve old warning if it exists
            if existing_alert:
                existing_alert.status = "RESOLVED"
                db.commit()

            new_alert = models.Alert(
                item_id=item.id,
                type="SHORTAGE",
                message=msg,
                severity="RED",
                status="ACTIVE",
                created_at=datetime.utcnow()
            )
            db.add(new_alert)
            db.commit()
    
    elif first_warning_day:
        severity = "YELLOW"
        msg = f"WARNING: Low stock risk around {first_warning_day.strftime('%d-%m-%Y')}"

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
            db.commit()
            
    else:
        # Resolve any active alert if stock is healthy now
        if existing_alert:
            existing_alert.status = "RESOLVED"
            existing_alert.resolution_note = "Stock levels are healthy in the 7-day forecast."
            db.commit()