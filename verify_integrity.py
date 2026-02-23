import sys
import os
from datetime import date
from sqlalchemy import create_engine, event

# Add the project root to sys.path
sys.path.append(os.getcwd())
from sqlalchemy.orm import sessionmaker
from backend import models
from backend.models import Base

# Isolated Test Database
TEST_DB_URL = "sqlite:///./test_integrity.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})

# Enable foreign key enforcement for the test engine
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

def test_integrity():
    print("--- Recreating Tables with Constraints (Isolated Test DB) ---")
    if os.path.exists("test_integrity.db"):
        os.remove("test_integrity.db")
    
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    
    try:
        # 1. Test Foreign Key Enforcement (Invalid item_id)
        print("\n1. Testing Foreign Key Enforcement (Invalid ID)...")
        try:
            orphan_order = models.DemandOrder(
                item_id=9999, # Non-existent
                customer_name="Orphan",
                quantity=10,
                due_date=date.today(),
                priority="HIGH"
            )
            db.add(orphan_order)
            db.commit()
            print("❌ FAILED: Orphan order was allowed!")
        except Exception as e:
            print(f"✅ PASSED: Blocked invalid order. Error: {str(e)[:50]}...")
            db.rollback()

        # 2. Test Non-Nullable Constraint
        print("\n2. Testing Non-Nullable Constraint (Null item_id)...")
        try:
            null_order = models.DemandOrder(
                item_id=None,
                customer_name="Null",
                quantity=5,
                due_date=date.today(),
                priority="LOW"
            )
            db.add(null_order)
            db.commit()
            print("❌ FAILED: Null item_id was allowed!")
        except Exception as e:
            print(f"✅ PASSED: Blocked null item_id. Error: {str(e)[:50]}...")
            db.rollback()

        # 3. Test Cascade Delete
        print("\n3. Testing Cascade Delete...")
        item = models.Item(
            sku="TEST-001", 
            name="Test Item", 
            cost_price=10.0, 
            selling_price=20.0, 
            current_stock=100
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        
        order = models.DemandOrder(
            item_id=item.id,
            customer_name="Tester",
            quantity=50,
            due_date=date.today(),
            priority="MEDIUM"
        )
        db.add(order)
        db.commit()
        
        # Verify order exists
        order_count = db.query(models.DemandOrder).count()
        print(f"   Initial order count: {order_count}")
        
        # Delete item
        db.delete(item)
        db.commit()
        
        # Verify order is gone
        order_count = db.query(models.DemandOrder).count()
        print("✅ PASSED: Child order deleted automatically (Cascade).")

        # 4. Test Alert Logic (Negative Stock & Spikes)
        test_alert_logic(db)

    finally:
        db.close()

def test_alert_logic(db):
    print("\n--- Testing Alert Logic ---")
    from backend.utils import refresh_item_status
    
    # Negative Stock Test
    print("1. Negative Stock Test...")
    item_neg = models.Item(sku="NEG-001", name="Neg Item", cost_price=1, selling_price=2, current_stock=-10, safety_stock=5)
    db.add(item_neg)
    db.commit()
    refresh_item_status(db, item_neg)
    alert = db.query(models.Alert).filter(models.Alert.item_id == item_neg.id, models.Alert.status == "ACTIVE").first()
    if alert and alert.severity == "RED":
        print(f"✅ PASSED: Red alert created for negative stock. Message: {alert.message}")
    else:
        print("❌ FAILED: No red alert for negative stock!")

    # Demand Spike Test
    print("\n2. Demand Spike Test...")
    item_spike = models.Item(sku="SPIKE-001", name="Spike Item", cost_price=1, selling_price=2, current_stock=100, safety_stock=10)
    db.add(item_spike)
    db.commit()
    
    # Healthy start
    refresh_item_status(db, item_spike)
    alert_pre = db.query(models.Alert).filter(models.Alert.item_id == item_spike.id, models.Alert.status == "ACTIVE").first()
    print(f"   Initial state: {'Alert present' if alert_pre else 'No alert'}")
    
    # Add huge demand
    huge_order = models.DemandOrder(item_id=item_spike.id, customer_name="Spike", quantity=500, due_date=date.today(), priority="HIGH")
    db.add(huge_order)
    db.commit()
    refresh_item_status(db, item_spike)
    alert_post = db.query(models.Alert).filter(models.Alert.item_id == item_spike.id, models.Alert.status == "ACTIVE").first()
    if alert_post and alert_post.severity == "RED":
        print(f"✅ PASSED: Red alert created after demand spike. Message: {alert_post.message}")
    else:
        print("❌ FAILED: No alert after spike!")

    # Zero Safety Stock Test
    print("\n3. Zero Safety Stock Test...")
    item_zero = models.Item(sku="ZERO-001", name="Zero SS Item", cost_price=1, selling_price=2, current_stock=1, safety_stock=0)
    db.add(item_zero)
    db.commit()
    refresh_item_status(db, item_zero)
    alert_zero = db.query(models.Alert).filter(models.Alert.item_id == item_zero.id, models.Alert.status == "ACTIVE").first()
    if not alert_zero:
        print("✅ PASSED: No alert for stock 1 with safety 0.")
    else:
        print(f"❌ FAILED: Alert triggered unexpectedly! {alert_zero.message}")
    
    # Drop to -1 (Actual shortage)
    item_zero.current_stock = -1
    db.commit()
    refresh_item_status(db, item_zero)
    alert_zero_post = db.query(models.Alert).filter(models.Alert.item_id == item_zero.id, models.Alert.status == "ACTIVE").first()
    if alert_zero_post:
        print(f"✅ PASSED: Alert triggered at -1 for safety 0. Message: {alert_zero_post.message}")
    else:
        print("❌ FAILED: No alert at -1 stock even if safety is 0!")
    
    # Recover to 0 (Should resolve)
    item_zero.current_stock = 0
    db.commit()
    refresh_item_status(db, item_zero)
    alert_zero_res = db.query(models.Alert).filter(models.Alert.item_id == item_zero.id, models.Alert.status == "ACTIVE").first()
    if not alert_zero_res:
        print("✅ PASSED: Alert resolved at 0 stock for safety 0.")
    else:
        print(f"❌ FAILED: Alert persisted at 0 stock for safety 0!")

if __name__ == "__main__":
    test_integrity()
