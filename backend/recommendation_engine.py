from backend import models


def generate_recommendation(db, item, projections):
    """
    Analyzes projections and recommends a replenishment quantity if needed.
    """

    # Horizon Stock Logic: Only recommend if the final day is still below safety.
    horizon_stock = projections[-1]["projected_stock"] if projections else item.current_stock

    # If horizon stock is healthy, resolve all pending recommendations
    if horizon_stock >= item.safety_stock:
        pending_recs = db.query(models.Recommendation).filter(
            models.Recommendation.item_id == item.id,
            models.Recommendation.status == "PENDING"
        ).all()
        for rec in pending_recs:
            rec.status = "RESOLVED"
        db.commit()
        return None

    # Find the minimum projected stock in the window to calculate required quantity
    min_stock = min(p["projected_stock"] for p in projections)

    # Calculate required quantity to restore safety stock at the minimum point
    required_quantity = item.safety_stock - min_stock

    # Respect minimum order quantity
    if required_quantity < item.min_order_qty:
        required_quantity = item.min_order_qty

    # Check if a pending recommendation already exists for this item
    existing_rec = db.query(models.Recommendation).filter(
        models.Recommendation.item_id == item.id,
        models.Recommendation.status == "PENDING"
    ).first()

    if existing_rec:
        # Update existing recommendation if the required quantity increased
        if required_quantity > existing_rec.recommended_qty:
            existing_rec.recommended_qty = required_quantity
            db.commit()
        return existing_rec

    # Create new recommendation
    new_rec = models.Recommendation(
        item_id=item.id,
        recommended_qty=int(required_quantity),
        status="PENDING"
    )

    db.add(new_rec)
    db.commit()

    return new_rec