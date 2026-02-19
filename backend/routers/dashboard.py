from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models
from backend.engine import calculate_projection

router = APIRouter(prefix="/api", tags=["Dashboard"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):

    items = db.query(models.Item).all()

    total_items = len(items)
    healthy = 0
    warning = 0
    critical = 0

    for item in items:

        demands = db.query(models.Demand).filter(
            models.Demand.item_id == item.id
        ).all()

        supplies = db.query(models.Supply).filter(
            models.Supply.item_id == item.id
        ).all()

        projection = calculate_projection(item, demands, supplies)

        lowest_stock = min(day["projected_stock"] for day in projection)

        if lowest_stock < 0:
            critical += 1
        elif lowest_stock < item.safety_stock:
            warning += 1
        else:
            healthy += 1

    active_alerts = db.query(models.Alert).filter(
        models.Alert.status == "ACTIVE"
    ).count()

    return {
        "total_items": total_items,
        "healthy_items": healthy,
        "warning_items": warning,
        "critical_items": critical,
        "active_alerts": active_alerts
    }
@router.get("/dashboard/supplier-risk")
def supplier_risk_dashboard(db: Session = Depends(get_db)):

    suppliers = db.query(models.Supplier).all()

    result = []

    for supplier in suppliers:

        if supplier.reliability_score < 0.5:
            risk = "HIGH"
        elif supplier.reliability_score < 0.8:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        result.append({
            "supplier_id": supplier.id,
            "name": supplier.name,
            "lead_time_days": supplier.lead_time_days,
            "reliability_score": supplier.reliability_score,
            "risk_level": risk
        })

    return result
