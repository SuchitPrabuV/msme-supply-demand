from backend.database import SessionLocal
from backend import models
from datetime import date, timedelta
import requests

def verify_receive():
    db = SessionLocal()
    try:
        # 1. Get initial state
        item = db.query(models.Item).filter(models.Item.sku == 'ITEM002').first()
        initial_stock = item.current_stock
        print(f"Initial Stock for ITEM002: {initial_stock}")

        # 2. Create a supply order
        new_order = models.SupplyOrder(
            item_id=item.id,
            supplier_name="Test Supplier",
            quantity=50,
            order_date=date.today() - timedelta(days=5),
            expected_delivery_date=date.today() - timedelta(days=1), # Overdue
            status="ORDERED"
        )
        db.add(new_order)
        db.commit()
        order_id = new_order.id
        print(f"Created Overdue Supply Order: {order_id} (Qty: 50)")

        # 3. Call the receive endpoint via requests (if server is running) or call the function directly
        # Since uvicorn is running, I can use requests
        BASE_URL = "http://127.0.0.1:8000"
        response = requests.post(f"{BASE_URL}/api/orders/supply/{order_id}/receive")
        
        if response.status_code == 200:
            print("Successfully called receive endpoint.")
            
            # 4. Verify stock and order deletion
            db.expire_all()
            updated_item = db.query(models.Item).filter(models.Item.sku == 'ITEM002').first()
            final_stock = updated_item.current_stock
            print(f"Final Stock: {final_stock}")
            
            order_exists = db.query(models.SupplyOrder).filter(models.SupplyOrder.id == order_id).first()
            if final_stock == initial_stock + 50 and not order_exists:
                print("Verification SUCCESS: Stock increased and order deleted.")
            else:
                print(f"Verification FAILED: Expected stock {initial_stock + 50}, got {final_stock}. Order exists: {bool(order_exists)}")
        else:
            print(f"Failed to call receive endpoint: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_receive()
