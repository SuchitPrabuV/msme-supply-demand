from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models

router = APIRouter(prefix="/api", tags=["Recommendations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# GET ALL PENDING RECOMMENDATIONS
@router.get("/recommendations")
def get_recommendations(db: Session = Depends(get_db)):

    recs = db.query(models.Recommendation).filter(
        models.Recommendation.status == "PENDING"
    ).all()

    return [
        {
            "id": rec.id,
            "item_name": rec.item.name if rec.item else None,
            "recommended_qty": rec.recommended_qty,
            "rationale": rec.rationale,
            "status": rec.status
        }
        for rec in recs
    ]


# APPROVE
@router.post("/recommendations/{rec_id}/approve")
def approve_recommendation(rec_id: int, db: Session = Depends(get_db)):
    from datetime import date, timedelta

    rec = db.query(models.Recommendation).filter(
        models.Recommendation.id == rec_id
    ).first()

    if not rec:
        return {"message": "Recommendation not found"}

    item = db.query(models.Item).filter(models.Item.id == rec.item_id).first()
    if not item:
        return {"message": "Item not found"}

    # 1️⃣ Change recommendation status
    rec.status = "APPROVED"

    # 2️⃣ Update Item Current Stock (Immediate Fix)
    # The user requested that approving should change the current stock.
    item.current_stock += rec.recommended_qty

    # 3️⃣ Create a Supply Order (Record of the action)
    delivery_date = date.today() + timedelta(days=item.lead_time)
    new_po = models.SupplyOrder(
        item_id=item.id,
        supplier_name="Recommended Supplier",
        quantity=rec.recommended_qty,
        order_date=date.today(),
        expected_delivery_date=delivery_date,
        status="RECEIVED" # Mark as received since we added to current stock
    )
    
    db.add(new_po)
    db.commit()

    # 4️⃣ Refresh item status to auto-resolve alerts
    from backend.utils import refresh_item_status
    refresh_item_status(db, item)

    return {"message": f"Recommendation approved. PO created for {rec.recommended_qty} units."}


# REJECT
@router.post("/{rec_id}/reject")
def reject_recommendation(rec_id: int, db: Session = Depends(get_db)):
    rec = db.query(models.Recommendation).filter(
        models.Recommendation.id == rec_id
    ).first()

    if not rec:
        return {"message": "Recommendation not found"}

    rec.status = "REJECTED"
    db.commit()

    return {"message": "Recommendation rejected"}
