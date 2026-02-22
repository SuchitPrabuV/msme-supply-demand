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


# ✅ THEN define routes
from backend.engine import calculate_projection

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):

    db = SessionLocal()
    items = db.query(models.Item).all()

    critical = 0
    warning = 0
    healthy = 0

    for item in items:

        projections = calculate_projection(db, item)
        min_projected_stock = min(p["projected_stock"] for p in projections)

        if min_projected_stock < item.safety_stock:
            critical += 1
        elif min_projected_stock < item.safety_stock * 1.5:
            warning += 1
        else:
            healthy += 1

        print(
            f"{item.sku} | Current: {item.current_stock} | "
            f"Min Projected: {min_projected_stock} | "
            f"Safety: {item.safety_stock}"
        )

    db.close()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "critical": critical,
            "warning": warning,
            "healthy": healthy,
            "items": items,
        }
    )

@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse(
        "upload.html",
        {"request": request, "preview_data": None}
    )


@app.get("/items-view", response_class=HTMLResponse)
def items_view(request: Request):
    db = SessionLocal()
    items = db.query(models.Item).all()
    db.close()
    return templates.TemplateResponse(
        "items.html",
        {"request": request, "items": items}
    )


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




@app.get("/demand-orders-view", response_class=HTMLResponse)
def demand_orders_view(request: Request):
    db = SessionLocal()
    orders = (
        db.query(models.DemandOrder)
        .options(joinedload(models.DemandOrder.item))
        .all()
    )
    db.close()
    return templates.TemplateResponse(
        "demand_orders.html",
        {"request": request, "orders": orders}
    )

@app.get("/supply-orders-view", response_class=HTMLResponse)
def supply_orders_view(request: Request):
    db = SessionLocal()
    orders = db.query(models.SupplyOrder).options(
        joinedload(models.SupplyOrder.item)
    ).all()

    db.close()
    return templates.TemplateResponse(
        "supply_orders.html",
        {"request": request, "orders": orders}
    )
