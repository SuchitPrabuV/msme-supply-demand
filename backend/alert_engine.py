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

        # Rule: YELLOW -> projected_stock < 1.5 * safety_stock
        elif stock < (item.safety_stock * 1.5):
            if first_warning_day is None:
                first_warning_day = p["date"]

    # Horizon stock (end of projection window)
    horizon_stock = projections[-1]["projected_stock"] if projections else item.current_stock

    # Rule check for RED (Critical): shortage detected AND stock is declining below safety
    is_red_needed = first_shortage_day is not None and horizon_stock < item.safety_stock

    # Rule check for YELLOW (Warning):
    # Stock must BOTH be in the warning band AND actively declining from its current level.
    # This prevents static inventories (no demand/supply) from triggering false warnings.
    warning_threshold = item.safety_stock * 1.5
    is_declining = horizon_stock < item.current_stock
    is_yellow_needed = (
        first_warning_day is not None
        and horizon_stock < warning_threshold
        and is_declining  # <-- KEY FIX: only warn if stock is moving downward
    )

    existing_alert = db.query(models.Alert).filter(
        models.Alert.item_id == item.id,
        models.Alert.type == "SHORTAGE",
        models.Alert.status == "ACTIVE"
    ).first()

    if is_red_needed:
        msg = f"CRITICAL [{item.sku} - {item.name}]: Stockout expected on {first_shortage_day.strftime('%d-%m-%Y')}"
        if not existing_alert:
            db.add(models.Alert(item_id=item.id, type="SHORTAGE", message=msg, severity="RED", status="ACTIVE", created_at=datetime.utcnow()))
        else:
            existing_alert.severity = "RED"
            existing_alert.message = msg
            existing_alert.status = "ACTIVE"
        db.commit()

    elif is_yellow_needed:
        msg = f"WARNING [{item.sku} - {item.name}]: Low stock risk around {first_warning_day.strftime('%d-%m-%Y')}"
        if not existing_alert:
            db.add(models.Alert(item_id=item.id, type="SHORTAGE", message=msg, severity="YELLOW", status="ACTIVE", created_at=datetime.utcnow()))
        else:
            existing_alert.severity = "YELLOW"
            existing_alert.message = msg
            existing_alert.status = "ACTIVE"
        db.commit()

    else:
        if existing_alert:
            existing_alert.status = "RESOLVED"
            existing_alert.resolution_note = "Stock levels are healthy."
            db.commit()
