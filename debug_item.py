from backend.database import SessionLocal
from backend import models

db = SessionLocal()
item = db.query(models.Item).filter(models.Item.sku == 'ITEM002').first()
if item:
    print(f"SKU: {item.sku}")
    print(f"Name: {item.name}")
    print(f"Current Stock: {item.current_stock}")
    print(f"Safety Stock: {item.safety_stock}")
    print(f"Multiplier: {item.reorder_target_multiplier}")
    
    rec = db.query(models.Recommendation).filter(
        models.Recommendation.item_id == item.id,
        models.Recommendation.status == 'PENDING'
    ).first()
    
    if rec:
        print(f"Rec Qty: {rec.recommended_qty}")
        print(f"Rec Rationale: {rec.rationale}")
    else:
        print("No pending recommendation found.")
db.close()
