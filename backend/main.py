from fastapi import FastAPI, Request
import os
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import joinedload

from backend import models
from backend.database import engine, Base, SessionLocal
from backend.routers.health import router as health_router
from backend.routers.items import router as items_router
from backend.routers.ingest import router as ingest_router
from backend.routers.flows import router as flows_router
from backend.routers.projection import router as projection_router
from backend.routers.alerts import router as alerts_router
from backend.routers.dashboard import router as dashboard_router
from backend.routers.recommendations import router as recommendations_router
from backend.routers.simulation import router as simulation_router
from backend.routers.orders import router as orders_router
from backend.routers.production import router as production_router
from backend.routers.export import router as export_router
from backend.routers.settings import router as settings_router
from backend.routers.suppliers import router as suppliers_router
from backend.routers.gmail import router as gmail_router
from backend.routers.chatbot import router as chatbot_router
from backend.engine import calculate_projection



app = FastAPI(title="MSME Supply Demand Control Tower")

# Template setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "frontend", "templates"))

# Create tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(health_router)
app.include_router(items_router)
app.include_router(ingest_router)
app.include_router(flows_router)
app.include_router(projection_router)
app.include_router(alerts_router)
app.include_router(dashboard_router)
app.include_router(recommendations_router)
app.include_router(simulation_router)
app.include_router(orders_router)
app.include_router(production_router)
app.include_router(export_router)
app.include_router(settings_router)
app.include_router(suppliers_router)
app.include_router(gmail_router)
app.include_router(chatbot_router)


# ✅ THEN define routes
from backend.engine import calculate_projection

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):

    db = SessionLocal()
    try:
        # Force global refresh to ensure alerts and recommendations match latest stock/orders
        from backend.utils import refresh_all_items_status
        refresh_all_items_status(db)
        
        # Categorize items with their alert messages
        items = db.query(models.Item).all()
        critical_items = []
        warning_items = []
        healthy_items = []

        for item in items:
            # Check for active alerts
            active_alerts = db.query(models.Alert).filter(models.Alert.item_id == item.id, models.Alert.status == "ACTIVE").all()
            
            # Get the most severe alert message
            red_alert = next((a for a in active_alerts if a.severity == "RED"), None)
            yellow_alert = next((a for a in active_alerts if a.severity == "YELLOW"), None)

            # Get pending recommendation
            rec = db.query(models.Recommendation).filter(
                models.Recommendation.item_id == item.id,
                models.Recommendation.status == "PENDING"
            ).first()

            if red_alert:
                critical_items.append({"item": item, "message": red_alert.message, "recommendation": rec})
            elif yellow_alert:
                warning_items.append({"item": item, "message": yellow_alert.message, "recommendation": rec})
            else:
                healthy_items.append({"item": item})

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "critical_items": critical_items,
                "warning_items": warning_items,
                "healthy_items": healthy_items,
                "total_items": len(items),
                "items": items # Keep for Quick Create dropdowns
            }
        )
    finally:
        db.close()

@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse(
        "upload.html",
        {"request": request, "preview_data": None}
    )


@app.get("/items-view", response_class=HTMLResponse)
def items_view(request: Request):
    db = SessionLocal()
    try:
        items = db.query(models.Item).options(joinedload(models.Item.supplier)).all()
        suppliers = db.query(models.Supplier).all()
        return templates.TemplateResponse(
            "items.html",
            {"request": request, "items": items, "suppliers": suppliers}
        )
    finally:
        db.close()


@app.get("/suppliers-view", response_class=HTMLResponse)
def suppliers_view(request: Request):
    db = SessionLocal()
    try:
        suppliers = db.query(models.Supplier).all()
        return templates.TemplateResponse(
            "suppliers.html",
            {"request": request, "suppliers": suppliers}
        )
    finally:
        db.close()


@app.get("/items/{item_id}", response_class=HTMLResponse)
def item_detail(request: Request, item_id: int):
    return templates.TemplateResponse(
        "item_detail.html",
        {"request": request, "item_id": item_id}
    )

@app.get("/debug/all-data")
def debug_all():
    db = SessionLocal()

    return {
        "items": db.query(models.Item).count(),
        "demand_orders": db.query(models.DemandOrder).count(),
        "supply_orders": db.query(models.SupplyOrder).count(),
        "production_runs": db.query(models.ProductionRun).count()
    }




@app.get("/simulation")
def simulation_view(request: Request):
    db = SessionLocal()
    try:
        items = db.query(models.Item).all()
        return templates.TemplateResponse("simulation.html", {"request": request, "items": items})
    finally:
        db.close()


@app.get("/demand-orders-view", response_class=HTMLResponse)
def demand_orders_view(request: Request):
    db = SessionLocal()
    try:
        orders = (
            db.query(models.DemandOrder)
            .options(joinedload(models.DemandOrder.item))
            .all()
        )
        
        # Apply priority sorting: HIGH > MEDIUM > LOW
        priority_map = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        orders = sorted(orders, key=lambda x: priority_map.get(x.priority, 3))
        
        items = db.query(models.Item).all()
        return templates.TemplateResponse(
            "demand_orders.html",
            {"request": request, "orders": orders, "items": items}
        )
    finally:
        db.close()

@app.get("/supply-orders-view", response_class=HTMLResponse)
def supply_orders_view(request: Request):
    db = SessionLocal()
    try:
        orders = db.query(models.SupplyOrder).options(
            joinedload(models.SupplyOrder.item)
        ).all()
        items = db.query(models.Item).options(joinedload(models.Item.supplier)).all()
        return templates.TemplateResponse(
            "supply_orders.html",
            {"request": request, "orders": orders, "items": items}
        )
    finally:
        db.close()

@app.get("/settings", response_class=HTMLResponse)
def settings_view(request: Request):
    db = SessionLocal()
    try:
        settings = db.query(models.Settings).first()
        if not settings:
            settings = models.Settings(sender_email="", app_password="", recipient_email="", alerts_enabled=True)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return templates.TemplateResponse(
            "settings.html",
            {"request": request, "settings": settings}
        )
    finally:
        db.close()
