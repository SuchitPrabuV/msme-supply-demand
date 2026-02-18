from datetime import date, timedelta

def calculate_projection(item, demands, supplies, days=7):
    today = date.today()
    stock = item.current_stock
    timeline = []

    for i in range(days):
        current_day = today + timedelta(days=i)

        daily_demand = sum(
            d.quantity for d in demands
            if d.demand_date == current_day
        )

        daily_supply = sum(
            s.quantity for s in supplies
            if s.supply_date == current_day
        )

        stock = stock - daily_demand + daily_supply

        timeline.append({
            "date": current_day.isoformat(),
            "projected_stock": stock
        })

    return timeline
