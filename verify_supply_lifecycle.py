from backend.database import SessionLocal
from backend import models
from backend import engine
from datetime import date, timedelta
import requests

BASE_URL = "http://127.0.0.1:8000/api"

def verify_supply_lifecycle():
    db = SessionLocal()
    try:
        item = db.query(models.Item).filter(models.Item.sku == 'ITEM001').first()
        
        # 1. Create a DRAFT supply order
        supply = models.SupplyOrder(
            item_id=item.id,
            supplier_name="Lifecycle Test",
            quantity=50,
            order_date=date.today(),
            expected_delivery_date=date.today() + timedelta(days=2),
            status="DRAFT"
        )
        db.add(supply)
        db.commit()
        print(f"Created DRAFT Supply Order ID {supply.id}")

        # 2. Check if DRAFT is ignored in projections
        projection = engine.calculate_projection(db, item)
        print(f"Projection contains {len(projection)} days.")
        # Find the day of expected delivery
        target_date = date.today() + timedelta(days=2)
        day_proj = next((p for p in projection if p['date'] == target_date), None)
        
        if not day_proj:
            print(f"DEBUG: Target date {target_date} not found in projection dates: {[p['date'] for p in projection]}")
        
        # Since it's draft, it should NOT be in 'supply'
        if day_proj and day_proj['supply'] == 0:
            print("✅ DRAFT correctly ignored in projections.")
        else:
            print(f"❌ DRAFT found in projections! Supply: {day_proj['supply'] if day_proj else 'None'}")

        # 3. Confirm the order (DRAFT -> ORDERED)
        print(f"Promoting ID {supply.id} to ORDERED...")
        resp = requests.post(f"{BASE_URL}/orders/supply/{supply.id}/order")
        if resp.status_code == 200:
            db.refresh(supply)
            projection = engine.calculate_projection(db, item)
            day_proj = next((p for p in projection if p['date'] == target_date), None)
            if supply.status == "ORDERED" and day_proj and day_proj['supply'] == 50:
                print("✅ Promotion to ORDERED verified and reflected in projections.")
            else:
                print(f"❌ Promotion FAILED. Status: {supply.status}, Proj Supply: {day_proj['supply'] if day_proj else 'None'}")
        else:
            print(f"❌ API Promotion FAILED: {resp.status_code}")

        # 4. Receive the order (ORDERED -> RECEIVED)
        initial_stock = item.current_stock
        print(f"Receiving ID {supply.id}...")
        resp = requests.post(f"{BASE_URL}/orders/supply/{supply.id}/receive")
        if resp.status_code == 200:
            db.refresh(item)
            db.refresh(supply)
            projection = engine.calculate_projection(db, item)
            day_proj = next((p for p in projection if p['date'] == target_date), None)
            if supply.status == "RECEIVED" and item.current_stock == initial_stock + 50 and (day_proj is None or day_proj['supply'] == 0):
                print("✅ Receipt verified: Stock updated, Status RECEIVED, removed from projections.")
            else:
                print(f"❌ Receipt FAILED. Status: {supply.status}, Stock: {item.current_stock}")
        else:
            print(f"❌ API Receipt FAILED: {resp.status_code}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_supply_lifecycle()
