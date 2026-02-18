from backend.database import SessionLocal
from backend import models

db = SessionLocal()
items = db.query(models.Item).all()

print(f"Total Items: {len(items)}")
for item in items:
    print(f"ID: {item.id}, SKU: {item.sku}, Name: {item.name}")

db.close()
