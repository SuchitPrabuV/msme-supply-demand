from backend.database import SessionLocal
from backend.utils import refresh_all_items_status

def run_refresh():
    db = SessionLocal()
    try:
        refresh_all_items_status(db)
        print("Successfully refreshed all item statuses.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_refresh()
