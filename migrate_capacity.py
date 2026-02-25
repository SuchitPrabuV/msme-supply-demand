import sqlite3
import os

db_path = "msme.db" # Correct DB from database.py

def migrate():
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Adding machine_capacity column...")
        cursor.execute("ALTER TABLE items ADD COLUMN machine_capacity FLOAT DEFAULT 100.0")
    except sqlite3.OperationalError as e:
        print(f"machine_capacity already exists or error: {e}")

    try:
        print("Adding shift_capacity column...")
        cursor.execute("ALTER TABLE items ADD COLUMN shift_capacity FLOAT DEFAULT 8.0")
    except sqlite3.OperationalError as e:
        print(f"shift_capacity already exists or error: {e}")

    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
