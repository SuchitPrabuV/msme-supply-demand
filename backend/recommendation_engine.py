from backend import models


def generate_recommendation(db, item, projections):
    """
    Analyzes projections and recommends a replenishment quantity if needed.
    """

    # Target Stock Logic: Use the dynamic reorder target multiplier
    target_stock = item.safety_stock * item.reorder_target_multiplier
    horizon_stock = projections[-1]["projected_stock"] if projections else item.current_stock

    # Resolve if current stock is healthy AND horizon reaches target
    if item.current_stock >= item.safety_stock and horizon_stock >= target_stock:
        pending_recs = db.query(models.Recommendation).filter(
            models.Recommendation.item_id == item.id,
            models.Recommendation.status == "PENDING"
        ).all()
        for rec in pending_recs:
            rec.status = "RESOLVED"
        db.commit()
        return None

    # Find the minimum projected stock and the day it occurs
    min_stock = item.current_stock
    stockout_date = None
    for p in projections:
        if p["projected_stock"] < min_stock:
            min_stock = p["projected_stock"]
        if p["projected_stock"] < item.safety_stock and stockout_date is None:
            stockout_date = p["date"]

    # Calculate required quantity to reach reorder target multiplier
    target_stock = item.safety_stock * item.reorder_target_multiplier
    required_quantity = max(0, target_stock - min_stock)

    # Respect minimum order quantity
    if required_quantity < item.min_order_qty:
        required_quantity = item.min_order_qty

    # Generate Rationale
    if stockout_date:
        rationale = f"To cover a stockout risk on {stockout_date.strftime('%d-%m-%Y')}. "
    else:
        rationale = "To restore safety stock levels. "
    
    rationale += f"Targeting {item.reorder_target_multiplier}x safety stock."

    # Check for unfillable demand orders (demand > current stock)
    unfillable_demand = db.query(models.DemandOrder).filter(
        models.DemandOrder.item_id == item.id,
        models.DemandOrder.status == "OPEN",
        models.DemandOrder.quantity > item.current_stock
    ).first()

    if unfillable_demand:
        rationale += " | Missing stock for demand order(s)"

    # Check if a pending recommendation already exists for this item
    existing_rec = db.query(models.Recommendation).filter(
        models.Recommendation.item_id == item.id,
        models.Recommendation.status == "PENDING"
    ).first()

    if existing_rec:
        # Update existing recommendation if the required quantity increased
        if required_quantity > existing_rec.recommended_qty:
            existing_rec.recommended_qty = int(required_quantity)
            existing_rec.rationale = rationale
            db.commit()
        return existing_rec

    # Create new recommendation
    new_rec = models.Recommendation(
        item_id=item.id,
        recommended_qty=int(required_quantity),
        rationale=rationale,
        status="PENDING"
    )

    db.add(new_rec)
    db.commit()

    return new_rec