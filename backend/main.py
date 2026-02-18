from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.database import engine, Base
from backend.routers.health import router as health_router
from backend.routers.items import router as items_router
from backend.routers.ingest import router as ingest_router
from backend import models
import os 


app = FastAPI(title="MSME Supply Demand Control Tower")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "frontend", "templates"))

Base.metadata.create_all(bind=engine)

app.include_router(health_router)
app.include_router(items_router)
app.include_router(ingest_router)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse(
        "upload.html",
        {"request": request, "preview_data": None}
    )