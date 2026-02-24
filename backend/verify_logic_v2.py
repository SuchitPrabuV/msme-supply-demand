from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend import models
from backend.recommendation_engine import generate_recommendation
from backend.alert_engine import run_alert_engine
from datetime import date, timedelta

def test_logic():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 1. Create a test item
    test_sku = "TEST-LOGIC-1"
    item = db.query(models.Item).filter(models.Item.sku == test_sku).first()
    if item:
        db.delete(item)
        db.commit()
    
    item = models.Item(
        sku=test_sku,
        name="Test Item Logic",
        cost_price=10.0,
        selling_price=20.0,
        current_stock=100,
        safety_stock=50,
        min_order_qty=10
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    print(f"Testing Item: {item.sku}, Stock: {item.current_stock}, Safety: {item.safety_stock}")

    # 2. Test Recommendation Rationale (Stockout scenario)
    projections_stockout = [
        {"day": 0, "date": date.today(), "projected_stock": 100},
        {"day": 1, "date": date.today() + timedelta(days=1), "projected_stock": 20}
    ]
    rec = generate_recommendation(db, item, projections_stockout)
    db.refresh(rec)
    print(f"Recommendation for Stockout: Qty={rec.recommended_qty}, Rationale='{rec.rationale}'")
    assert "To cover a stockout risk on" in rec.rationale

    # 3. Test Overstock Alert
    projections_overstock = [
        {"day": 0, "date": date.today(), "projected_stock": 200},
        {"day": 1, "date": date.today() + timedelta(days=1), "projected_stock": 200}
    ]
    # Stock 200 > 3 * 50 (150)
    run_alert_engine(db, item, projections_overstock)
    alert = db.query(models.Alert).filter(models.Alert.item_id == item.id, models.Alert.type == "OVERSTOCK", models.Alert.status == "ACTIVE").first()
    print(f"Overstock Alert: {alert.message if alert else 'NOT FOUND'}")
    assert alert is not None
    assert "OVERSTOCK" in alert.message

    # Cleanup
    db.delete(item)
    db.commit()
    db.close()
    print("Verification Successful!")

if __name__ == "__main__":
    test_logic()
