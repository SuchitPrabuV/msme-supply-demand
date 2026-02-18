from backend import models
from datetime import datetime


def run_alert_engine(db, item, projection):

    shortage_detected = False

    for day in projection:
        if day["projected_stock"] < item.safety_stock:
            shortage_detected = True
            break

    existing_alert = db.query(models.Alert).filter(
        models.Alert.item_id == item.id,
        models.Alert.type == "SHORTAGE",
        models.Alert.status == "ACTIVE"
    ).first()

    if shortage_detected and not existing_alert:
        new_alert = models.Alert(
            item_id=item.id,
            type="SHORTAGE",
            message="Projected stock will fall below safety stock",
            severity="RED",
            status="ACTIVE",
            created_at=datetime.utcnow()
        )
        db.add(new_alert)
        db.commit()

    if not shortage_detected and existing_alert:
        existing_alert.status = "RESOLVED"
        existing_alert.resolution_note = "Stock level recovered"
        db.commit()
