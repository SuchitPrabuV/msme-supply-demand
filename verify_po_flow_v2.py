import sys
import os
from datetime import date, timedelta

# Mocking FastAPI and other dependencies if needed, or just using DB
from backend.database import SessionLocal
from backend import models
from backend.routers.recommendations import approve_recommendation

def verify_po_flow_v2():
    db = SessionLocal()
    try:
        print("--- Verification V2 Started ---")

        # 1. Create or get test supplier
        supplier_name = "Test Automation Supplier V2"
        supplier = db.query(models.Supplier).filter(models.Supplier.name == supplier_name).first()
        if not supplier:
            supplier = models.Supplier(
                name=supplier_name,
                contact_email="test-supplier-v2@example.com",
                lead_time_days=5
            )
            db.add(supplier)
            db.commit()
            db.refresh(supplier)
            print(f"Created test supplier: {supplier.name} (ID: {supplier.id})")
        else:
            print(f"Using existing test supplier: {supplier.name} (ID: {supplier.id})")

        # 2. Create test item anchored to this supplier
        sku = "TEST-PO-SKU-V2"
        item = db.query(models.Item).filter(models.Item.sku == sku).first()
        if item:
            db.delete(item)
            db.commit()
        
        item = models.Item(
            sku=sku,
            name="Test PO Item V2",
            current_stock=50, # Set healthy stock initially
            safety_stock=20,
            cost_price=10.0,
            selling_price=15.0,
            supplier_id=supplier.id
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        print(f"Created test item: {item.sku} linked to {supplier.name} (Supplier ID: {item.supplier_id})")

        # 3. Create a pending recommendation
        rec = models.Recommendation(
            item_id=item.id,
            recommended_qty=100,
            rationale="Test stockout risk V2",
            status="PENDING"
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        print(f"Created pending recommendation ID: {rec.id}")

        # 4. Approve the recommendation
        print("Approving recommendation...")
        initial_stock = item.current_stock
        result = approve_recommendation(rec.id, db)
        print(f"Result: {result['message']}")

        # Re-fetch item to check stock
        db.refresh(item)
        print(f"Stock after approval: {item.current_stock} (Initial: {initial_stock})")
        if item.current_stock == initial_stock:
            print("SUCCESS: Inventory NOT modified during approval.")
        else:
            print("FAILURE: Inventory modified during approval!")

        # 5. Verify Supply Order creation
        po = db.query(models.SupplyOrder).filter(
            models.SupplyOrder.item_id == item.id,
            models.SupplyOrder.quantity == 100,
            models.SupplyOrder.status == "ORDERED"
        ).first()

        if po:
            print(f"SUCCESS: Supply Order (PO) found with ID: {po.id}")
            print(f"PO Supplier Name: {po.supplier_name}")
            print(f"PO Supplier ID: {po.supplier_id}")
            if po.supplier_id == supplier.id:
                print("SUCCESS: Supplier ID correctly linked in SupplyOrder.")
            else:
                print(f"FAILURE: Expected supplier ID {supplier.id}, got {po.supplier_id}")
        else:
            print("FAILURE: No Supply Order found in ORDERED status.")

        # 6. Receive the order
        from backend.routers.orders import receive_supply_order
        print("Receiving supply order...")
        receive_result = receive_supply_order(po.id, db)
        print(f"Receive Result: {receive_result['message']}")

        # Re-fetch item to check stock
        db.refresh(item)
        print(f"Stock after receiving: {item.current_stock}")
        if item.current_stock == initial_stock + 100:
            print("SUCCESS: Inventory correctly updated upon receiving.")
        else:
            print(f"FAILURE: Inventory incorrect. Expected {initial_stock + 100}, got {item.current_stock}")

    except Exception as e:
        print(f"ERROR during verification: {e}")
    finally:
        db.close()
        print("--- Verification V2 Finished ---")

if __name__ == "__main__":
    verify_po_flow_v2()
