from backend.engine import calculate_projection
from backend.alert_engine import run_alert_engine
from backend.recommendation_engine import generate_recommendation

from backend import models

def refresh_item_status(db, item):
    """
    Recalculates projections, updates alerts, and generates/updates recommendations
    for a given item. Call this after any change to inventory or orders.
    """
    # Dynamic Horizon: Look ahead lead_time + buffer, min 14 days
    horizon = max(14, item.lead_time + 7)
    projections = calculate_projection(db, item, forecast_days=horizon)
    run_alert_engine(db, item, projections)
    generate_recommendation(db, item, projections)

def refresh_all_items_status(db):
    """
    Refreshes the status of all items in the database.
    """
    items = db.query(models.Item).all()
    for item in items:
        refresh_item_status(db, item)
