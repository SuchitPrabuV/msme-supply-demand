from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.database import engine, Base, SessionLocal
from backend.routers.health import router as health_router
from backend.routers.items import router as items_router
from backend.routers.ingest import router as ingest_router
from backend.models import Item
import os
from backend.routers.flows import router as flows_router
from backend.routers.projection import router as projection_router
from backend.routers.alerts import router as alerts_router


# ✅ FIRST create app
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



# ✅ THEN define routes
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):

    db = SessionLocal()
    items = db.query(Item).all()

    critical = 0
    warning = 0
    healthy = 0

    for item in items:
        if item.current_stock < item.safety_stock:
            critical += 1
        elif item.current_stock <= item.safety_stock * 1.2:
            warning += 1
        else:
            healthy += 1

    db.close()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "critical": critical,
            "warning": warning,
            "healthy": healthy
        }
    )


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse(
        "upload.html",
        {"request": request, "preview_data": None}
    )
