from backend import models
from datetime import datetime


def run_alert_engine(db, item, projections):
    """
    Scans the projection for stockout risks.
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

        # Rule: YELLOW -> projected_stock < 3.0 * safety_stock
        elif stock < (item.safety_stock * 3.0):
            if first_warning_day is None:
                first_warning_day = p["date"]

    # Horizon stock (end of projection window)
    horizon_stock = projections[-1]["projected_stock"] if projections else item.current_stock

    # Rule check for RED (Critical): 
    # 1. Immediate Shortage (stock already below safety)
    # 2. Unmitigated Future Shortage (horizon still below safety)
    is_red_needed = (item.current_stock < item.safety_stock) or (first_shortage_day is not None and horizon_stock < item.safety_stock)

    # Rule check for YELLOW (Warning):
    # 1. Mitigated FUTURE risk: current is fine, but future was bad and is now fixed by PO
    # 2. Warning band: horizon stock is in the safety-to-warning range
    warning_threshold = item.safety_stock * 3.0
    
    is_mitigated_future_risk = (not is_red_needed and first_shortage_day is not None and horizon_stock >= item.safety_stock)
    is_warning_band = (not is_red_needed and first_warning_day is not None and horizon_stock < warning_threshold)
    
    is_yellow_needed = is_mitigated_future_risk or is_warning_band

    # Rule check for OVERSTOCK:
    # Trigger if projected stock exceeds safety stock * 6.0 (Hardcoded)
    overstock_threshold = item.safety_stock * 6.0
    is_overstock_needed = (
        horizon_stock > overstock_threshold 
        and item.current_stock >= item.safety_stock 
        and item.safety_stock > 0
    )

    # 1. Manage SHORTAGE alerts
    existing_shortage_alert = db.query(models.Alert).filter(
        models.Alert.item_id == item.id,
        models.Alert.type == "SHORTAGE",
        models.Alert.status == "ACTIVE"
    ).first()

    today = datetime.utcnow().date()

    if is_red_needed:
        if first_shortage_day:
            days_to_stockout = (first_shortage_day - today).days
            if days_to_stockout <= 0:
                msg = f"CRITICAL [{item.sku} - {item.name}]: Item IS stocked out ({first_shortage_day.strftime('%d/%m')})"
            else:
                msg = f"CRITICAL [{item.sku} - {item.name}]: Stockout risk on {first_shortage_day.strftime('%d/%m')}"
        else:
            msg = f"CRITICAL [{item.sku} - {item.name}]: Immediate stockout risk"

        if not existing_shortage_alert:
            db.add(models.Alert(item_id=item.id, type="SHORTAGE", message=msg, severity="RED", status="ACTIVE", created_at=datetime.utcnow()))
        else:
            existing_shortage_alert.severity = "RED"
            existing_shortage_alert.message = msg
        db.commit()

    elif is_yellow_needed:
        if is_mitigated_future_risk:
            # Analyze why it's mitigated (horizon stock is healthy)
            msg = f"WARNING [{item.sku} - {item.name}]: Temporary gap mitigated by incoming supply"
        else:
            date_str = first_warning_day.strftime('%d/%m') if first_warning_day else "N/A"
            msg = f"WARNING [{item.sku} - {item.name}]: Low stock risk on {date_str}"
        
        if not existing_shortage_alert:
            db.add(models.Alert(item_id=item.id, type="SHORTAGE", message=msg, severity="YELLOW", status="ACTIVE", created_at=datetime.utcnow()))
        else:
            existing_shortage_alert.severity = "YELLOW"
            existing_shortage_alert.message = msg
        db.commit()

    else:
        if existing_shortage_alert:
            existing_shortage_alert.status = "RESOLVED"
            existing_shortage_alert.resolution_note = "Stock levels are healthy."
            db.commit()

    # 2. Manage OVERSTOCK alerts
    existing_overstock_alert = db.query(models.Alert).filter(
        models.Alert.item_id == item.id,
        models.Alert.type == "OVERSTOCK",
        models.Alert.status == "ACTIVE"
    ).first()

    if is_overstock_needed:
        msg = f"OVERSTOCK [{item.sku} - {item.name}]: Projected stock ({int(horizon_stock)}) is > {item.overstock_multiplier}x safety stock."
        if not existing_overstock_alert:
            db.add(models.Alert(item_id=item.id, type="OVERSTOCK", message=msg, severity="YELLOW", status="ACTIVE", created_at=datetime.utcnow()))
        else:
            existing_overstock_alert.message = msg
        db.commit()
    else:
        if existing_overstock_alert:
            existing_overstock_alert.status = "RESOLVED"
            existing_overstock_alert.resolution_note = "Stock levels normalized."
            db.commit()
