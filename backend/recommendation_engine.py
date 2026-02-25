from backend import models


def generate_recommendation(db, item, projections):
    """
    Analyzes projections and recommends a replenishment quantity if needed.
    """

    # Hardcoded Logic: Use 3.0x safety stock as trigger and target
    target_stock = item.safety_stock * 3.0
    warning_threshold = item.safety_stock * 3.0 # Trigger as soon as we drop below 3x
    horizon_stock = projections[-1]["projected_stock"] if projections else item.current_stock

    # Resolution Logic: 
    # Resolve if current stock is healthy (>= 3x) AND horizon reaches target (>= 3x)
    
    # 1. Find min stock in the horizon
    min_stock = item.current_stock
    stockout_date = None
    for p in projections:
        if p["projected_stock"] < min_stock:
            min_stock = p["projected_stock"]
        if p["projected_stock"] < item.safety_stock and stockout_date is None:
            stockout_date = p["date"]

    # Resolution condition: Horizon is healthy or current status is clearly fine
    if item.current_stock >= warning_threshold and horizon_stock >= target_stock:
        pending_recs = db.query(models.Recommendation).filter(
            models.Recommendation.item_id == item.id,
            models.Recommendation.status == "PENDING"
        ).all()
        for rec in pending_recs:
            rec.status = "RESOLVED"
        db.commit()
        return None

    # Check for unfillable demand orders (demand > current stock)
    unfillable_demand = db.query(models.DemandOrder).filter(
        models.DemandOrder.item_id == item.id,
        models.DemandOrder.status == "OPEN",
        models.DemandOrder.quantity > item.current_stock
    ).first()

    # TRIGGER Logic: Do not generate a NEW recommendation if we are still at or above 3x
    # Unless there is an unfillable demand order
    existing_rec = db.query(models.Recommendation).filter(
        models.Recommendation.item_id == item.id,
        models.Recommendation.status == "PENDING"
    ).first()

    if not unfillable_demand and min_stock >= warning_threshold:
        if existing_rec:
            # If it was existing but we are now at/above 3x, resolve it
            existing_rec.status = "RESOLVED"
            db.commit()
        return None

    # Calculate required quantity to reach 3x target
    required_quantity = max(0, target_stock - min_stock)

    # Respect minimum order qty (hardcoded to 1 if we removed UI for it, but model still has it)
    final_rec_qty = max(required_quantity, item.min_order_qty or 1)

    # ... (rest of logic remains same, just using hardcoded 3.0)
    # Scan for EXPEDITING Logic...
    late_order = None
    if stockout_date:
        # Find earliest supply that could cover the gap if expedited
        late_supply = db.query(models.SupplyOrder).filter(
            models.SupplyOrder.item_id == item.id,
            models.SupplyOrder.status == "ORDERED",
            models.SupplyOrder.expected_delivery_date > stockout_date
        ).order_by(models.SupplyOrder.expected_delivery_date).first()

        late_production = db.query(models.ProductionRun).filter(
            models.ProductionRun.item_id == item.id,
            models.ProductionRun.status.in_(["PLANNED", "IN_PROGRESS"]),
            models.ProductionRun.end_date > stockout_date
        ).order_by(models.ProductionRun.end_date).first()
        
        if late_supply:
            late_order = f"Supply Order from {late_supply.supplier_name or 'Supplier'}"
            order_date = late_supply.expected_delivery_date
        elif late_production:
            late_order = f"Production Run #{late_production.id}"
            order_date = late_production.end_date

    # Generate Rationale
    if late_order:
        rationale = f"EXPEDITE: Pull in {late_order} (scheduled for {order_date.strftime('%d-%m')}) to cover stockout risk on {stockout_date.strftime('%d-%m')}."
        final_rec_qty = 0 
    elif stockout_date:
        rationale = f"To cover a stockout risk on {stockout_date.strftime('%d-%m-%Y')}. "
        rationale += "Targeting 3.0x safety stock."
    else:
        rationale = "To restore inventory buffer to target levels. "
        rationale += "Targeting 3.0x safety stock."

    if unfillable_demand:
        rationale += " | Missing stock for demand order(s)"

    if existing_rec:
        if final_rec_qty != existing_rec.recommended_qty or rationale != existing_rec.rationale:
            existing_rec.recommended_qty = int(final_rec_qty)
            existing_rec.rationale = rationale
            db.commit()
        return existing_rec

    # Create new recommendation
    new_rec = models.Recommendation(
        item_id=item.id,
        recommended_qty=int(final_rec_qty),
        rationale=rationale,
        status="PENDING"
    )

    db.add(new_rec)
    db.commit()

    return new_rec