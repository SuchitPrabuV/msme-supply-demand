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

    return [
        {
            "id": alert.id,
            "item_name": alert.item.name if alert.item else None,
            "type": alert.type,
            "message": alert.message,
            "severity": alert.severity,
            "status": alert.status
        }
        for alert in alerts
    ]


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()

    if alert:
        alert.status = "RESOLVED"
        alert.resolution_note = "Resolved manually"
        db.commit()

    return {"message": "Alert resolved"}

    