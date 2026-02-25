from backend.database import SessionLocal
from backend import models
from backend.routers.orders import calculate_priority

def migrate_priorities():
    db = SessionLocal()
    try:
        orders = db.query(models.DemandOrder).filter(models.DemandOrder.status == "OPEN").all()
        print(f"Updating {len(orders)} open demand orders...")
        
        for o in orders:
            old_p = o.priority
            new_p = calculate_priority(o.due_date)
            if old_p != new_p:
                print(f"ID {o.id}: {old_p} -> {new_p}")
                o.priority = new_p
        
        db.commit()
        print("Update complete.")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_priorities()
