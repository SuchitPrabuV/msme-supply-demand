from backend.database import SessionLocal
from backend import models
from datetime import date, timedelta

db = SessionLocal()
item = db.query(models.Item).filter(models.Item.sku == 'ITEM001').first()
if item:
    print(f"Item: {item.sku}, ID: {item.id}")
    seven_days_ago = date.today() - timedelta(days=7)
    demands = db.query(models.Demand).filter(models.Demand.item_id == item.id).all()
    print(f"All items in demands table for {item.sku}:")
    for d in demands:
        print(f"  ID: {d.id}, Qty: {d.quantity}, Date: {d.demand_date}")
    
    total_demand = sum(d.quantity for d in demands if d.demand_date >= seven_days_ago)
    print(f"Total demand in last 7 days (since {seven_days_ago}): {total_demand}")
else:
    print("ITEM001 not found")

item2 = db.query(models.Item).filter(models.Item.sku == 'ITEM002').first()
if item2:
    print(f"Item: {item2.sku}, ID: {item2.id}, Stock: {item2.current_stock}, Safety: {item2.safety_stock}")

db.close()
