from backend.database import SessionLocal
from backend import models
from backend.engine import calculate_projection
from backend.recommendation_engine import generate_recommendation

db = SessionLocal()
item = db.query(models.Item).filter(models.Item.sku == 'ITEM005').first()

if item:
    print(f"SKU: {item.sku}")
    print(f"Name: {item.name}")
    print(f"Current Stock: {item.current_stock}")
    print(f"Safety Stock: {item.safety_stock}")
    
    projections = calculate_projection(db, item)
    print("\nProjections (First 5 days):")
    for p in projections[:5]:
        print(f"Day {p['day']} ({p['date']}): Stock {p['projected_stock']}, Demand {p['demand']}, Supply {p['supply']}")

    # Check for existing recommendations
    rec = db.query(models.Recommendation).filter(
        models.Recommendation.item_id == item.id,
        models.Recommendation.status == "PENDING"
    ).first()
    
    if rec:
        print(f"\nExisting Pending Recommendation:")
        print(f"Qty: {rec.recommended_qty}")
        print(f"Rationale: {rec.rationale}")
    else:
        print("\nNo pending recommendation found.")

    # Re-run generation logic to see what happens
    print("\nRe-generating recommendation...")
    new_rec = generate_recommendation(db, item, projections)
    if new_rec:
        print(f"New/Updated Recommendation Qty: {new_rec.recommended_qty}")
        print(f"Rationale: {new_rec.rationale}")

db.close()
