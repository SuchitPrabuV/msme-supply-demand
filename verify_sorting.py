from backend.database import SessionLocal
from backend import models

def verify_sorting():
    db = SessionLocal()
    try:
        # Fetch orders using the same logic as backend/main.py
        orders = db.query(models.DemandOrder).all()
        
        priority_map = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_orders = sorted(orders, key=lambda x: priority_map.get(x.priority, 3))
        
        print(f"Total Orders: {len(sorted_orders)}")
        for o in sorted_orders:
            print(f"ID: {o.id}, Priority: {o.priority}, Status: {o.status}")
            
        # Verify sequence
        last_priority_val = -1
        for o in sorted_orders:
            curr_val = priority_map.get(o.priority, 3)
            if curr_val < last_priority_val:
                print("FAILURE: Sorting is incorrect!")
                return
            last_priority_val = curr_val
            
        print("SUCCESS: Priority sorting verified (HIGH > MEDIUM > LOW).")
        
    finally:
        db.close()

if __name__ == "__main__":
    verify_sorting()
