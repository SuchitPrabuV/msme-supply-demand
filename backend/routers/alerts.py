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
