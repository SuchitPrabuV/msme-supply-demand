from backend.database import SessionLocal
from backend import models, schemas
from backend.routers.orders import calculate_priority
from datetime import date, timedelta

def verify_auto_priority():
    today = date.today()
    
    test_cases = [
        (today + timedelta(days=0), "HIGH"),
        (today + timedelta(days=2), "HIGH"),
        (today + timedelta(days=3), "MEDIUM"),
        (today + timedelta(days=5), "MEDIUM"),
        (today + timedelta(days=6), "LOW"),
        (today + timedelta(days=10), "LOW"),
    ]
    
    print("Verifying Priority Logic:")
    for due_date, expected in test_cases:
        actual = calculate_priority(due_date)
        status = "PASSED" if actual == expected else "FAILED"
        print(f"Due Date: {due_date} (in {(due_date - today).days} days) -> Expected: {expected}, Actual: {actual} ... {status}")

if __name__ == "__main__":
    verify_auto_priority()
