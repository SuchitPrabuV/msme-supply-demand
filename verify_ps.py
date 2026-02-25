from backend.database import SessionLocal
from backend import models
from backend.utils import refresh_item_status
from datetime import date, timedelta
import requests

def verify_ps_alignment():
    db = SessionLocal()
    try:
        # 1. Prepare Item
        item = db.query(models.Item).filter(models.Item.sku == 'ITEM002').first()
        item.current_stock = 50
        item.safety_stock = 30
        db.commit()
        print(f"Setting ITEM002 Stock: 50, Safety: 30")

        # 2. Create Demand Order causing stockout in 3 days
        stockout_date = date.today() + timedelta(days=3)
        demand = models.DemandOrder(
            item_id=item.id,
            customer_name="PS Test Customer",
            quantity=60, # 50 - 60 = -10
            due_date=stockout_date,
            priority="HIGH",
            status="OPEN"
        )
        db.add(demand)
        
        # 3. Create Late Supply Order (in 6 days)
        late_supply = models.SupplyOrder(
            item_id=item.id,
            supplier_name="Late Supplier Ltd",
            quantity=100,
            order_date=date.today(),
            expected_delivery_date=date.today() + timedelta(days=6),
            status="ORDERED"
        )
        db.add(late_supply)
        db.commit()

        print(f"Created Demand (Qty 60) in 3 days. Created Supply (Qty 100) in 6 days.")

        # 4. Trigger Refresh
        refresh_item_status(db, item)
        db.expire_all()

        # 5. Check Alert
        alert = db.query(models.Alert).filter(models.Alert.item_id == item.id, models.Alert.status == "ACTIVE").first()
        if alert:
            print(f"VERIFIED ALERT: {alert.message}")
        else:
            print("FAILED: No active alert found.")

        # 6. Check Recommendation
        rec = db.query(models.Recommendation).filter(models.Recommendation.item_id == item.id, models.Recommendation.status == "PENDING").first()
        if rec:
            print(f"VERIFIED RECOMMENDATION: {rec.rationale}")
            if "EXPEDITE" in rec.rationale:
                print("✅ Expedite logic works!")
            else:
                print("❌ Expedite logic FAILED (suggested new order).")
        else:
            print("FAILED: No pending recommendation found.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        db.query(models.DemandOrder).filter(models.DemandOrder.customer_name == "PS Test Customer").delete()
        db.query(models.SupplyOrder).filter(models.SupplyOrder.supplier_name == "Late Supplier Ltd").delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    verify_ps_alignment()
