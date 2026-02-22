import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import engine, Base, SessionLocal
from backend import models
from datetime import date

def reset_db_and_verify():
    # 1. Reset Database
    print("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 2. Create Test Item
        item = models.Item(
            sku="TEST-SKU",
            name="Test Item",
            current_stock=100,
            cost_price=10.0,
            selling_price=20.0
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        print(f"Created Item: {item.sku}")
        
        # 3. Create Supply Order (New String-based Supplier)
        order = models.SupplyOrder(
            item_id=item.id,
            supplier_name="Global Widgets Corp",
            quantity=50,
            order_date=date.today(),
            expected_delivery_date=date.today(),
            status="ORDERED"
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        print(f"Created Supply Order. Supplier: {order.supplier_name}")
        
        # 4. Verify Retrieval
        retrieved = db.query(models.SupplyOrder).first()
        if retrieved.supplier_name == "Global Widgets Corp":
            print("✅ Supplier removal verification SUCCESSFUL!")
        else:
            print("❌ Supplier removal verification FAILED!")
            
    finally:
        db.close()

if __name__ == "__main__":
    reset_db_and_verify()
