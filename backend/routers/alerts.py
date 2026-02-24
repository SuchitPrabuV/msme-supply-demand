from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from backend.database import SessionLocal
from backend import models, schemas

router = APIRouter(prefix="/api", tags=["Alerts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/alerts/{item_id}", response_model=List[schemas.AlertResponse])
def get_alerts(item_id: int, db: Session = Depends(get_db)):
    alerts = db.query(models.Alert).filter(
        models.Alert.item_id == item_id
    ).all()

    return alerts


@router.get("/alerts")
def get_active_alerts(db: Session = Depends(get_db)):
    alerts = db.query(models.Alert).filter(models.Alert.status == "ACTIVE").all()

    results = []
    for alert in alerts:
        # Get pending recommendation for this item
        rec = db.query(models.Recommendation).filter(
            models.Recommendation.item_id == alert.item_id,
            models.Recommendation.status == "PENDING"
        ).first()

        # Fallback for Overstock or other alerts without a formal recommendation
        rec_data = None
        if rec:
            rec_data = {
                "id": rec.id,
                "recommended_qty": rec.recommended_qty,
                "rationale": rec.rationale
            }
        elif alert.type == "OVERSTOCK":
            rec_data = {
                "id": None,
                "recommended_qty": 0,
                "rationale": "Excess stock detected. Recommend pausing replenishment and monitoring demand."
            }

        results.append({
            "id": alert.id,
            "item_name": alert.item.name if alert.item else None,
            "sku": alert.item.sku if alert.item else None,
            "type": alert.type,
            "message": alert.message,
            "severity": alert.severity,
            "status": alert.status,
            "recommendation": rec_data
        })

    return results


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()

    if alert:
        alert.status = "RESOLVED"
        alert.resolution_note = "Resolved manually"
        db.commit()

    return {"message": "Alert resolved"}

    