from backend.database import SessionLocal
from backend import models, engine, recommendation_engine, alert_engine
from datetime import date

def diagnose(sku):
    db = SessionLocal()
    try:
        item = db.query(models.Item).filter(models.Item.sku == sku).first()
        if not item:
            print(f"Item {sku} not found.")
            return

        print(f"--- Diagnostic for {item.sku} ({item.name}) ---")
        print(f"Current Stock: {item.current_stock}")
        print(f"Safety Stock: {item.safety_stock}")
        print(f"Min Order Qty: {item.min_order_qty}")
        print(f"Multiplier: {item.reorder_target_multiplier}")
        
        target = item.safety_stock * item.reorder_target_multiplier
        print(f"Target Stock: {target}")

        # Trigger Engines
        proj = engine.calculate_projection(db, item)
        recommendation_engine.generate_recommendation(db, item, proj)
        alert_engine.run_alert_engine(db, item, proj)
        db.commit()

        # Recommendations
        rec = db.query(models.Recommendation).filter(models.Recommendation.item_id == item.id, models.Recommendation.status == 'PENDING').first()
        if rec:
            print(f"Pending Recommendation: {rec.recommended_qty} units")
            print(f"Rationale: {rec.rationale}")
        else:
            print("No pending recommendation.")

        # Alerts
        alerts = db.query(models.Alert).filter(models.Alert.item_id == item.id, models.Alert.status == 'ACTIVE').all()
        if alerts:
            for a in alerts:
                print(f"Active Alert: {a.type} - {a.message}")
        else:
            print("No active alerts.")

        # Projection
        proj = engine.calculate_projection(db, item)
        print("\n--- Projection (Next 7 Days) ---")
        for p in proj[:7]:
            print(f"{p['date']}: Stock {p['projected_stock']}, Demand {p['demand']}, Supply {p['supply']}")

    finally:
        db.close()

if __name__ == "__main__":
    import sys
    sku = sys.argv[1] if len(sys.argv) > 1 else "ITEM001"
    diagnose(sku)
