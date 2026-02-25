from backend.database import SessionLocal
from backend import models

def update_multipliers():
    db = SessionLocal()
    try:
        items = db.query(models.Item).all()
        for item in items:
            item.reorder_target_multiplier = 3.0
            print(f"Updated {item.sku}: 3.0")
        db.commit()
        print("Successfully updated all items to 3x multiplier target.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_multipliers()
