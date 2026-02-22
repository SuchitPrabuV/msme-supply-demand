from backend.engine import calculate_projection
from backend.alert_engine import run_alert_engine
from backend.recommendation_engine import generate_recommendation

def refresh_item_status(db, item):
    """
    Recalculates projections, updates alerts, and generates/updates recommendations
    for a given item. Call this after any change to inventory or orders.
    """
    projections = calculate_projection(db, item)
    run_alert_engine(db, item, projections)
    generate_recommendation(db, item, projections)
