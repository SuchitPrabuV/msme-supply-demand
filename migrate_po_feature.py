import sqlite3
import os

DB_PATH = "msme.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Starting migration...")

    # 1. Create suppliers table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        contact_email TEXT,
        lead_time_days INTEGER DEFAULT 7,
        reliability_score REAL DEFAULT 1.0
    )
    """)
    print("Checked/Created 'suppliers' table.")

    # 2. Add supplier_id to items table
    try:
        cursor.execute("ALTER TABLE items ADD COLUMN supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL")
        print("Added 'supplier_id' column to 'items' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("'supplier_id' column already exists in 'items' table.")
        else:
            print(f"Error adding column to items: {e}")

    try:
        cursor.execute("ALTER TABLE supply_orders ADD COLUMN supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL")
        print("Added 'supplier_id' column to 'supply_orders' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("'supplier_id' column already exists in 'supply_orders' table.")
        else:
            print(f"Error adding column to supply_orders: {e}")

    # 3. Create a default supplier for existing items
    cursor.execute("INSERT OR IGNORE INTO suppliers (name, contact_email) VALUES (?, ?)", ("Default Supplier", "admin@example.com"))
    cursor.execute("SELECT id FROM suppliers WHERE name = ?", ("Default Supplier",))
    supplier_id = cursor.fetchone()[0]

    # 4. Link existing items to the default supplier if they don't have one
    cursor.execute("UPDATE items SET supplier_id = ? WHERE supplier_id IS NULL", (supplier_id,))
    print(f"Linked existing items to default supplier (ID: {supplier_id}).")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
