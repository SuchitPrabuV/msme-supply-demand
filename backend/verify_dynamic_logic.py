from backend.database import SessionLocal, engine
from backend import models
from backend.utils import refresh_item_status
from datetime import date, timedelta, datetime
from backend.engine import calculate_projection

def verify_dynamic_logic():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 1. Setup Test Item
    test_sku = "V-DYNAMIC-1"
    item = db.query(models.Item).filter(models.Item.sku == test_sku).first()
    if item:
        db.delete(item)
        db.commit()
    
    item = models.Item(
        sku=test_sku,
        name="Dynamic Test Item",
        current_stock=100,
        safety_stock=50,
        min_order_qty=10,
        overstock_multiplier=5,
        lead_time=12,
        warning_multiplier=2.5
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    print(f"--- Step 1: Item Setup ---")
    print(f"SKU: {item.sku}, LeadTime: {item.lead_time}, WarningMult: {item.warning_multiplier}, OverstockMult: {item.overstock_multiplier}")

    # 2. Verify Lead Time in PO Creation
    print(f"\n--- Step 2: Verify Lead Time in Recommendation Approval ---")
    # Force a recommendation
    rec = models.Recommendation(
        item_id=item.id,
        recommended_qty=100,
        rationale="Test",
        status="PENDING"
    )
    db.add(rec)
    db.commit()
    
    # Approve via API logic (simulated)
    from backend.routers.recommendations import approve_recommendation
    approve_recommendation(rec.id, db)
    
    po = db.query(models.SupplyOrder).filter(models.SupplyOrder.item_id == item.id).first()
    expected_delivery = date.today() + timedelta(days=item.lead_time)
    print(f"PO Delivery Date: {po.expected_delivery_date}, Expected: {expected_delivery}")
    assert po.expected_delivery_date == expected_delivery

    # 3. Verify Warning Multiplier Alert
    print(f"\n--- Step 3: Verify Warning Multiplier Alert ---")
    # Stock = 100, Safety = 50, WarningMult = 2.5. Warning Threshold = 125.
    # We need stock < 125 AND stock < current_stock (declining)
    item.current_stock = 150
    db.commit()
    
    # Create a projected decline
    # Add a demand order for tomorrow
    order = models.DemandOrder(
        item_id=item.id,
        customer_name="Test",
        quantity=30, # 150 - 30 = 120 (below 125 threshold)
        due_date=date.today() + timedelta(days=1),
        priority="MEDIUM",
        status="OPEN"
    )
    db.add(order)
    db.commit()
    
    # Run alert engine
    projections = calculate_projection(db, item)
    from backend.alert_engine import run_alert_engine
    run_alert_engine(db, item, projections)
    
    alert = db.query(models.Alert).filter(
        models.Alert.item_id == item.id,
        models.Alert.type == "SHORTAGE",
        models.Alert.status == "ACTIVE"
    ).first()
    
    print(f"Alert Severity: {alert.severity if alert else 'NONE'}")
    assert alert.severity == "YELLOW"
    assert "Low stock risk" in alert.message

    # 4. Verify Overstock Message Multiplier
    print(f"\n--- Step 4: Verify Overstock Message Multiplier ---")
    # Stock = 150, Safety = 50, OverstockMult = 5. Threshold = 250.
    item.current_stock = 300
    db.commit()
    
    projections = calculate_projection(db, item)
    run_alert_engine(db, item, projections)
    
    overstock_alert = db.query(models.Alert).filter(
        models.Alert.item_id == item.id,
        models.Alert.type == "OVERSTOCK",
        models.Alert.status == "ACTIVE"
    ).first()
    
    print(f"Overstock Message: {overstock_alert.message if overstock_alert else 'NONE'}")
    assert f"> {item.overstock_multiplier}x" in overstock_alert.message

    print("\n✅ DYNAMIC LOGIC VERIFICATION SUCCESSFUL")
    
    # Cleanup
    db.delete(order)
    db.delete(po)
    db.delete(rec)
    db.delete(item)
    db.commit()
    db.close()

if __name__ == "__main__":
    verify_dynamic_logic()
