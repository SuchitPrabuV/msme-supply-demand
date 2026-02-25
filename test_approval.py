from backend.database import SessionLocal
from backend import models, engine, recommendation_engine
from backend.routers.recommendations import approve_recommendation
from datetime import date

def test_approval():
    db = SessionLocal()
    try:
        # 1. Setup - find recruitment for ITEM001
        item = db.query(models.Item).filter(models.Item.sku == 'ITEM001').first()
        rec = db.query(models.Recommendation).filter(
            models.Recommendation.item_id == item.id,
            models.Recommendation.status == 'PENDING'
        ).first()
        
        if not rec:
            print("No pending recommendation found for ITEM001. Running engine...")
            proj = engine.calculate_projection(db, item)
            rec = recommendation_engine.generate_recommendation(db, item, proj)
            db.commit()

        initial_stock = item.current_stock
        rec_qty = rec.recommended_qty
        print(f"Initial Stock: {initial_stock}")
        print(f"Recommendation Qty: {rec_qty}")

        # 2. Approve
        print("Approving recommendation...")
        result = approve_recommendation(rec.id, db)
        print(f"Result: {result}")

        # 3. Verify
        # Check stock (should NOT change)
        db.refresh(item)
        print(f"Stock After Approval: {item.current_stock} (Should be {initial_stock})")
        
        # Check Supply Order (should be ORDERED)
        latest_po = db.query(models.SupplyOrder).filter(
            models.SupplyOrder.item_id == item.id
        ).order_by(models.SupplyOrder.id.desc()).first()
        
        print(f"Latest PO Status: {latest_po.status} (Should be ORDERED)")
        print(f"Latest PO Qty: {latest_po.quantity} (Should be {rec_qty})")

        # Cleanup test PO if needed, or leave for manual check
        
    finally:
        db.close()

if __name__ == "__main__":
    test_approval()
