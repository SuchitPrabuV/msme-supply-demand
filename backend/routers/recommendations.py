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
            "status": rec.status
        }
        for rec in recs
    ]


# APPROVE
@router.post("/recommendations/{rec_id}/approve")
def approve_recommendation(rec_id: int, db: Session = Depends(get_db)):

    rec = db.query(models.Recommendation).filter(
        models.Recommendation.id == rec_id
    ).first()

    if not rec:
        return {"message": "Recommendation not found"}

    # 1️⃣ Change recommendation status
    rec.status = "APPROVED"

    # 2️⃣ Increase stock
    item = db.query(models.Item).filter(
        models.Item.id == rec.item_id
    ).first()

    if item:
        item.current_stock += rec.recommended_qty

    db.commit()

    return {"message": "Recommendation approved and stock updated"}
