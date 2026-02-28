import sys
import os
from datetime import date, timedelta

# Mocking FastAPI and other dependencies if needed, or just using DB
from backend.database import SessionLocal
from backend import models
from backend.routers.recommendations import approve_recommendation

def verify_po_flow():
    db = SessionLocal()
    try:
        print("--- Verification Started ---")

        # 1. Create or get test supplier
        supplier_name = "Test Automation Supplier"
        supplier = db.query(models.Supplier).filter(models.Supplier.name == supplier_name).first()
        if not supplier:
            supplier = models.Supplier(
                name=supplier_name,
                contact_email="test-supplier@example.com",
                lead_time_days=5
            )
            db.add(supplier)
            db.commit()
            db.refresh(supplier)
            print(f"Created test supplier: {supplier.name}")
        else:
            print(f"Using existing test supplier: {supplier.name}")

        # 2. Create test item anchored to this supplier
        sku = "TEST-PO-SKU"
        item = db.query(models.Item).filter(models.Item.sku == sku).first()
        if item:
            db.delete(item)
            db.commit()
        
        item = models.Item(
            sku=sku,
            name="Test PO Item",
            current_stock=10,
            safety_stock=20,
            cost_price=10.0,
            selling_price=15.0,
            supplier_id=supplier.id
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        print(f"Created test item: {item.sku} linked to {supplier.name}")

        # 3. Create a pending recommendation
        rec = models.Recommendation(
            item_id=item.id,
            recommended_qty=50,
            rationale="Test stockout risk",
            status="PENDING"
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        print(f"Created pending recommendation ID: {rec.id}")

        # 4. Approve the recommendation
        print("Approving recommendation...")
        result = approve_recommendation(rec.id, db)
        print(f"Result: {result['message']}")

        # 5. Verify Supply Order creation
        po = db.query(models.SupplyOrder).filter(
            models.SupplyOrder.item_id == item.id,
            models.SupplyOrder.quantity == 50
        ).first()

        if po:
            print(f"SUCCESS: Supply Order (PO) found with ID: {po.id}")
            print(f"PO Supplier Name: {po.supplier_name}")
            if po.supplier_name == supplier_name:
                print("SUCCESS: Supplier name correctly mapped from Item's linked supplier.")
            else:
                print(f"FAILURE: Expected supplier {supplier_name}, got {po.supplier_name}")
        else:
            print("FAILURE: No Supply Order created.")

    except Exception as e:
        print(f"ERROR during verification: {e}")
    finally:
        db.close()
        print("--- Verification Finished ---")

if __name__ == "__main__":
    verify_po_flow()
