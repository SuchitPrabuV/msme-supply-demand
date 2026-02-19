from datetime import timedelta, date


def calculate_projection(item, demands, supplies):

    today = min((d.demand_date for d in demands), default=None)

    if not today:
        today = min((s.supply_date for s in supplies), default=None)

    if not today:
        today = date.today()

    projection = []
    current_stock = item.current_stock

    demand_by_date = {}
    for demand in demands:
        key = demand.demand_date
        demand_by_date[key] = demand_by_date.get(key, 0) + demand.quantity

    supply_by_date = {}
    for supply in supplies:
        key = supply.supply_date
        supply_by_date[key] = supply_by_date.get(key, 0) + supply.quantity

    for i in range(7):
        day = today + timedelta(days=i)

        demand_qty = demand_by_date.get(day, 0)
        supply_qty = supply_by_date.get(day, 0)

        current_stock = current_stock - demand_qty + supply_qty

        projection.append({
            "date": day.isoformat(),
            "projected_stock": current_stock
        })

    return projection
