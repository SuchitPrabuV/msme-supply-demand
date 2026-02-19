from backend import models


def generate_recommendation(db, item, projection):

    lowest_stock = min(day["projected_stock"] for day in projection)

    if lowest_stock >= item.safety_stock:
        return None

    required_quantity = item.safety_stock - lowest_stock

    if required_quantity < item.min_order_qty:
        required_quantity = item.min_order_qty

    # Check if already pending recommendation exists
    existing_rec = db.query(models.Recommendation).filter(
        models.Recommendation.item_id == item.id,
        models.Recommendation.status == "PENDING"
    ).first()

    if existing_rec:
        return existing_rec

    # Create new recommendation
    new_rec = models.Recommendation(
        item_id=item.id,
        recommended_qty=required_quantity,
        status="PENDING"
    )

    db.add(new_rec)
    db.commit()

    return new_rec
