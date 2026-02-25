from backend.database import SessionLocal
from backend import models
import requests

BASE_URL = "http://127.0.0.1:8000/api/orders/demand"

def verify_demand_refinements():
    db = SessionLocal()
    try:
        print("--- Verifying Priority Sorting ---")
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            orders = response.json()
            priorities = [o['priority'] for o in orders if o['status'] == 'OPEN']
            print(f"Open Orders Priority Order: {priorities}")
            
            # Check if HIGH comes before others
            is_sorted = True
            priority_map = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            last_p = -1
            for p in priorities:
                curr_p = priority_map.get(p, 3)
                if curr_p < last_p:
                    is_sorted = False
                last_p = curr_p
            
            if is_sorted:
                print("✅ Sorting verified: HIGH > MEDIUM > LOW.")
            else:
                print("❌ Sorting FAILED.")
        else:
            print(f"Failed to fetch orders: {response.status_code}")

        print("\n--- Verifying Edit Restriction on Approved Orders ---")
        approved_order = db.query(models.DemandOrder).filter(models.DemandOrder.status == 'APPROVED').first()
        if approved_order:
            order_id = approved_order.id
            print(f"Attempting to edit Approved Order ID {order_id}...")
            edit_response = requests.put(f"{BASE_URL}/{order_id}", json={"customer_name": "Should Fail"})
            
            if edit_response.status_code == 400:
                print(f"✅ Edit blocked as expected: {edit_response.status_code} - {edit_response.json()['detail']}")
            else:
                print(f"❌ Edit NOT blocked: {edit_response.status_code}")
        else:
            print("No approved orders found to test edit restriction.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_demand_refinements()
