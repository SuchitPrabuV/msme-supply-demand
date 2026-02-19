def generate_recommendation(item, projection):

    lowest_stock = min(day["projected_stock"] for day in projection)

    if lowest_stock >= item.safety_stock:
        return {
            "action": "NONE",
            "message": "No immediate action required."
        }

    required_quantity = item.safety_stock - lowest_stock

    if required_quantity < item.min_order_qty:
        required_quantity = item.min_order_qty

    return {
        "action": "REORDER",
        "recommended_quantity": required_quantity,
        "message": f"Recommended to reorder at least {required_quantity} units."
    }
