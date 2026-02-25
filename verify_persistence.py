from backend.database import SessionLocal
from backend import models
from datetime import date, timedelta
import requests

BASE_URL = "http://127.0.0.1:8000/api"

def verify_persistence():
    db = SessionLocal()
    try:
        # --- Supply Persistence Test ---
        item = db.query(models.Item).filter(models.Item.sku == 'ITEM001').first()
        initial_stock = item.current_stock
        
        supply = models.SupplyOrder(
            item_id=item.id,
            supplier_name="Persistence Test",
            quantity=10,
            order_date=date.today(),
            expected_delivery_date=date.today() + timedelta(days=1),
            status="ORDERED"
        )
        db.add(supply)
        db.commit()
        
        print(f"Testing Supply Persistence for ID {supply.id}...")
        resp = requests.post(f"{BASE_URL}/orders/supply/{supply.id}/receive")
        
        if resp.status_code == 200:
            db.refresh(item)
            db.refresh(supply)
            if item.current_stock == initial_stock + 10 and supply.status == "RECEIVED":
                print("✅ Supply Persistence verified: Status is RECEIVED and stock updated.")
            else:
                print(f"❌ Supply Persistence logic FAILED. Stock: {item.current_stock}, Status: {supply.status}")
        else:
            print(f"❌ Supply Persistence API FAILED: {resp.status_code}")

        # --- Production Approval Test ---
        initial_stock = item.current_stock
        run = models.ProductionRun(
            item_id=item.id,
            quantity=20,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            status="PLANNED"
        )
        db.add(run)
        db.commit()

        print(f"\nTesting Production Approval for ID {run.id}...")
        resp = requests.post(f"{BASE_URL}/production/{run.id}/complete")
        
        if resp.status_code == 200:
            db.refresh(item)
            db.refresh(run)
            if item.current_stock == initial_stock + 20 and run.status == "COMPLETED":
                print("✅ Production Approval verified: Status is COMPLETED and stock updated.")
            else:
                print(f"❌ Production Approval logic FAILED. Stock: {item.current_stock}, Status: {run.status}")
        else:
            print(f"❌ Production Approval API FAILED: {resp.status_code}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_persistence()
