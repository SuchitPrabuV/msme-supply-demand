from fastapi import FastAPI
from backend.database import engine, Base
from backend.routers.health import router as health_router
from backend import models
from backend.routers.items import router as items_router


app = FastAPI(title="MSME Supply Demand Control Tower")

Base.metadata.create_all(bind=engine)

app.include_router(health_router)
app.include_router(items_router)

