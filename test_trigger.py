from backend.database import SessionLocal
from backend import models, engine, recommendation_engine
from datetime import date

def test_trigger():
    db = SessionLocal()
    try:
        item = db.query(models.Item).filter(models.Item.sku == 'ITEM001').first()
        original_stock = item.current_stock
        
        print(f"Original Stock: {original_stock}")
        
        # Drop stock to 25 (Below 30 warning)
        item.current_stock = 25
        db.commit()
        print("Dropped stock to 25. Running engine...")
        
        proj = engine.calculate_projection(db, item)
        rec = recommendation_engine.generate_recommendation(db, item, proj)
        
        if rec and rec.status == 'PENDING':
            print(f"✅ Recommendation Triggered: {rec.recommended_qty} units")
            print(f"Rationale: {rec.rationale}")
        else:
            print("❌ Recommendation NOT triggered!")

        # Restore
        item.current_stock = original_stock
        db.commit()
        print("Restored original stock.")

    finally:
        db.close()

if __name__ == "__main__":
    test_trigger()
