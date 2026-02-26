from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models
from pydantic import BaseModel

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatMessage(BaseModel):
    message: str

@router.post("/")
def chat(payload: ChatMessage, db: Session = Depends(get_db)):
    msg = payload.message.lower()
    
    # 1. Simple Conversational Greetings
    if msg in ["hi", "hello", "hey", "greetings", "good morning", "good afternoon"]:
        return {"reply": "Hello there! How can I help you with your supply chain today?"}
    if "how are you" in msg:
        return {"reply": "I'm just a bot, but I'm doing well! Keeping an eye on your inventory. What do you need?"}
    if any(k == msg for k in ["thanks", "thank you", "ok", "okay", "got it"]):
        return {"reply": "You're very welcome! 🌟 Let me know if you need anything else."}

    # 2. Entity Extraction: Check if they explicitly mentioned ANY product by name or SKU
    all_items = db.query(models.Item).all()
    found_item = None
    for item in all_items:
        if item.name.lower() in msg or item.sku.lower() in msg:
            found_item = item
            break
            
    if found_item:
        from sqlalchemy import func
        pending_sp = db.query(func.sum(models.SupplyOrder.quantity)).filter(models.SupplyOrder.item_id == found_item.id, models.SupplyOrder.status != "DELIVERED").scalar() or 0
        pending_dm = db.query(func.sum(models.DemandOrder.quantity)).filter(models.DemandOrder.item_id == found_item.id, models.DemandOrder.status != "COMPLETED").scalar() or 0
        
        alerts = db.query(models.Alert).filter(models.Alert.item_id == found_item.id, models.Alert.status == "ACTIVE").all()
        alert_text = ", ".join([a.message for a in alerts]) if alerts else "None ✅"
        stock_status = "⚠️ Low" if found_item.current_stock < found_item.safety_stock else "✅ OK"
        
        reply = f"📦 **Details for {found_item.name} ({found_item.sku})**:\n"
        reply += f"• **Stock:** {found_item.current_stock} (Safety: {found_item.safety_stock}) - {stock_status}\n"
        reply += f"• **Pending Supply:** {int(pending_sp)} units incoming\n"
        reply += f"• **Pending Demand:** {int(pending_dm)} units outgoing\n"
        reply += f"• **Active Alerts:** {alert_text}"
        return {"reply": reply}
        
    # 3. Supply Orders
    if any(k in msg for k in ["supply", "purchase", "buying", "inbound"]) and any(k in msg for k in ["order", "status", "list", "show", "any"]):
        orders = db.query(models.SupplyOrder).filter(models.SupplyOrder.status != "DELIVERED").limit(5).all()
        if not orders:
            return {"reply": "There are no pending supply orders currently."}
        reply_lines = ["📦 **Recent Supply Orders:**"]
        for o in orders:
            item_name = o.item.name if o.item else f"Item {o.item_id}"
            reply_lines.append(f"• {o.quantity}x {item_name} from {o.supplier_name or 'Unknown'} (Status: **{o.status}**)")
        return {"reply": "\n".join(reply_lines)}
        
    # 4. Demand Orders
    elif any(k in msg for k in ["demand", "sales", "customer", "outbound"]) and any(k in msg for k in ["order", "status", "list", "show", "any"]):
        orders = db.query(models.DemandOrder).filter(models.DemandOrder.status != "COMPLETED").limit(5).all()
        if not orders:
            return {"reply": "There are no pending demand orders currently."}
        reply_lines = ["🛍️ **Recent Demand Orders:**"]
        for o in orders:
            item_name = o.item.name if o.item else f"Item {o.item_id}"
            reply_lines.append(f"• {o.quantity}x {item_name} for {o.customer_name} (Status: **{o.status}**)")
        return {"reply": "\n".join(reply_lines)}
        
    # 5. Low Stock specific query
    elif any(k in msg for k in ["low stock", "shortage", "running out", "need to buy"]):
        items = db.query(models.Item).filter(models.Item.current_stock < models.Item.safety_stock).limit(5).all()
        if not items:
            return {"reply": "🎉 Great news! No items are currently below their safety stock levels."}
        reply_lines = ["📉 **Low Stock Items:**"]
        for i in items:
            reply_lines.append(f"• **{i.name}**: {i.current_stock} (Min required: {i.safety_stock})")
        return {"reply": "\n".join(reply_lines)}
             
    # 6. Inventory / Stock
    elif any(k in msg for k in ["inventory", "stock", "items", "warehouse"]):
        items = db.query(models.Item).limit(5).all()
        if not items:
            return {"reply": "There are no items in inventory."}
        reply_lines = ["🏭 **Inventory Status (Quick View):**"]
        for i in items:
            status = "⚠️ Low" if i.current_stock < i.safety_stock else "✅ OK"
            reply_lines.append(f"• **{i.name}**: {i.current_stock} in stock (Safety: {i.safety_stock}) - {status}")
        return {"reply": "\n".join(reply_lines)}
        
    # 7. Production Runs
    elif any(k in msg for k in ["production", "run", "manufacturing"]):
        runs = db.query(models.ProductionRun).filter(models.ProductionRun.status != "COMPLETED").limit(5).all()
        if not runs:
            return {"reply": "There are no active production runs."}
        reply_lines = ["⚙️ **Active Production Runs:**"]
        for r in runs:
            item_name = r.item.name if r.item else f"Item {r.item_id}"
            reply_lines.append(f"• {r.quantity}x {item_name} (Status: **{r.status}**)")
        return {"reply": "\n".join(reply_lines)}
        
    # 8. Alerts
    elif any(k in msg for k in ["alert", "warning", "critical", "danger"]):
        alerts = db.query(models.Alert).filter(models.Alert.status == "ACTIVE").limit(5).all()
        if not alerts:
            return {"reply": "✅ There are no active alerts. Everything is running smoothly!"}
        reply_lines = ["🚨 **Active Alerts:**"]
        for a in alerts:
            item_name = a.item.name if a.item else f"Item {a.item_id}"
            icon = "🔴" if a.severity == "RED" else "🟡"
            reply_lines.append(f"{icon} **{item_name}**: {a.message}")
        return {"reply": "\n".join(reply_lines)}

    # 9. Recommendations
    elif any(k in msg for k in ["recommend", "suggestion", "advice"]):
        recs = db.query(models.Recommendation).filter(models.Recommendation.status == "PENDING").limit(5).all()
        if not recs:
            return {"reply": "There are no pending recommendations at the moment."}
        reply_lines = ["💡 **Top Recommendations:**"]
        for r in recs:
            item_name = r.item.name if r.item else f"Item {r.item_id}"
            reply_lines.append(f"• **{item_name}**: {r.rationale} (Suggest: {r.recommended_qty})")
        return {"reply": "\n".join(reply_lines)}
        
    # 10. Help / Capabilities
    elif any(k in msg for k in ["help", "what can you do", "features", "capabilities", "menu"]):
        return {"reply": "Here are the features I currently support:\n\n1. 📦 **Check Supply Orders** (e.g., 'Show supply orders')\n2. 🛍️ **Check Demand Orders** (e.g., 'Recent sales orders')\n3. 🏭 **Check Inventory** (e.g., 'What is in stock?')\n4. 📉 **Low Stock Alerts** (e.g., 'What is running low?')\n5. ⚙️ **Track Production** (e.g., 'Show active production runs')\n6. 🚨 **Monitor Alerts** (e.g., 'Are there any critical warnings?')\n7. 💡 **Get Recommendations** (e.g., 'Give me some system advice')\n8. 🔍 **Item Lookups** (e.g., 'Give me details on Copper Wire')"}
        
    else:
        return {"reply": "👋 I may not have understood that completely.\n\nYou can ask me direct questions like:\n- *'Give me the status of Copper Wire'*\n- *'Show supply orders'*\n- *'What is low on stock?'*\n- *'Show active alerts'*"}
