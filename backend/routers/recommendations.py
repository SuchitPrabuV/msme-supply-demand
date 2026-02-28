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

    # 2️⃣ Determine Supplier
    # Use the supplier linked to the item, or fall back to "Default Supplier"
    supplier_name = "Default Supplier"
    supplier_id = None
    if item.supplier:
        supplier_id = item.supplier.id
        supplier_name = item.supplier.name

    # 3️⃣ Create a Supply Order (Record of the action)
    lead_time_days = 7
    if item.supplier:
        lead_time_days = item.supplier.lead_time_days or 7
    elif item.lead_time:
        lead_time_days = item.lead_time

    delivery_date = date.today() + timedelta(days=lead_time_days)
    new_po = models.SupplyOrder(
        item_id=item.id,
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        quantity=rec.recommended_qty,
        order_date=date.today(),
        expected_delivery_date=delivery_date,
        status="ORDERED"
    )
    
    db.add(new_po)
    db.commit()
    db.refresh(new_po)

    # 4️⃣ Trigger PO Email to Supplier
    from backend.email_service import send_po_email
    send_po_email(db, new_po.id)

    # 5️⃣ Refresh item status to auto-resolve alerts
    from backend.utils import refresh_item_status
    refresh_item_status(db, item)

    return {"message": f"Recommendation approved. PO created for {rec.recommended_qty} units and sent to {supplier_name}."}


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
