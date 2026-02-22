import sys
import os
from datetime import date, timedelta

# Add parent directory to path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, Base, engine
from backend import models
from backend.engine import calculate_projection

def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 1. Create a sample item
    item = models.Item(
        sku="TEST-01",
        name="Test Item",
        current_stock=100,
        safety_stock=50,
        cost_price=10.0,
        selling_price=20.0,
        min_order_qty=20
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    # 2. Add a demand order for Day 2 (100 units) -> Should cause stockout (100 - 100 = 0 < 50)
    today = date.today()
    demand = models.DemandOrder(
        item_id=item.id,
        customer_name="Customer A",
        quantity=100,
        due_date=today + timedelta(days=2),
        priority="HIGH",
        status="OPEN"
    )
    db.add(demand)
    
    # 3. Add a supply order for Day 4 (80 units) -> Should recover stock (0 + 80 = 80 > 50)
    supply = models.SupplyOrder(
        item_id=item.id,
        supplier_name="Test Supplier",
        quantity=20,
        order_date=date.today() - timedelta(days=2),
        expected_delivery_date=date.today() + timedelta(days=3),
        status="ORDERED"
    )
    db.add(supply)
    
    # 4. Add a production run for Day 5 (30 units) -> Stock becomes 110
    prod = models.ProductionRun(
        item_id=item.id,
        quantity=30,
        start_date=today,
        end_date=today + timedelta(days=5),
        status="PLANNED"
    )
    db.add(prod)
    
    db.commit()
    return db, item

def verify():
    db, item = setup_test_db()
    projections = calculate_projection(db, item)
    
    print(f"Verifying projections for {item.sku}:")
    for p in projections:
        print(f"Day {p['day']} ({p['date']}): Stock={p['projected_stock']} (D:{p['demand']}, S:{p['supply']})")
    
    # Asserts
    assert projections[0]["projected_stock"] == 100, "Day 0 should be current stock"
    assert projections[1]["projected_stock"] == 100, "Day 1 should be 100"
    assert projections[2]["projected_stock"] == 0, "Day 2 should be 0 due to demand"
    assert projections[3]["projected_stock"] == 0, "Day 3 should be 0"
    assert projections[4]["projected_stock"] == 80, "Day 4 should be 80 due to supply"
    assert projections[5]["projected_stock"] == 110, "Day 5 should be 110 due to production"
    
    print("\n✅ Projection logic PASSED!")
    db.close()

if __name__ == "__main__":
    try:
        verify()
    except Exception as e:
        print(f"\n❌ Verification FAILED: {e}")
        sys.exit(1)
