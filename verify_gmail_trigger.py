from unittest.mock import patch, MagicMock
from backend.database import SessionLocal
from backend import models, email_service, alert_engine
from datetime import datetime, timedelta

def verify_email_trigger():
    db = SessionLocal()
    try:
        # 1. Setup Mock Item with Critical Risk
        item = db.query(models.Item).filter(models.Item.sku == "ITEM001").first()
        if not item:
            print("ITEM001 not found. Skipping test.")
            return

        # Ensure settings exist
        settings = db.query(models.Settings).first()
        if not settings:
            settings = models.Settings(
                sender_email="test@gmail.com",
                app_password="test_password",
                recipient_email="owner@example.com",
                alerts_enabled=True
            )
            db.add(settings)
            db.commit()

        # 2. Mock projections showing immediate stockout
        today = datetime.utcnow().date()
        projections = [
            {"date": today, "projected_stock": -5, "demand": 10, "supply": 0}
        ]

        # 3. Patch the email service
        with patch("backend.email_service.send_critical_alert_email") as mock_send:
            # Delete existing alerts for clean run
            db.query(models.Alert).filter(models.Alert.item_id == item.id).delete()
            db.commit()

            print(f"Running alert engine for {item.sku}...")
            # We also need a recommendation in the DB for this item
            db.query(models.Recommendation).filter(models.Recommendation.item_id == item.id).delete()
            db.add(models.Recommendation(
                item_id=item.id,
                recommended_qty=100,
                rationale="Test Rationale: Urgent supply needed.",
                status="PENDING",
                created_at=datetime.utcnow()
            ))
            db.commit()

            alert_engine.run_alert_engine(db, item, projections)

            # 4. Verify trigger
            if mock_send.called:
                print("SUCCESS: Email trigger fired for new Critical Alert!")
                args, kwargs = mock_send.call_args
                print(f"Args: {args[1:]} (Item id, Item Name, SKU, Message)")
                # Check if item_id (first arg after db) is passed
                if args[1] == item.id:
                    print("PASSED: Item ID correctly passed to email service.")
            else:
                print("FAILED: Email trigger did not fire.")

    finally:
        db.close()

if __name__ == "__main__":
    verify_email_trigger()
