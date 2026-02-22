from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from typing import List
import os

from backend.database import SessionLocal
from backend import models, schemas
from backend.utils import refresh_item_status

router = APIRouter(prefix="/api/production", tags=["Production"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "frontend", "templates"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.ProductionRunUpdate])
def get_production_runs(db: Session = Depends(get_db)):
    return db.query(models.ProductionRun).options(joinedload(models.ProductionRun.item)).all()

@router.put("/{run_id}")
def update_production_run(run_id: int, run_update: schemas.ProductionRunUpdate, db: Session = Depends(get_db)):
    db_run = db.query(models.ProductionRun).filter(models.ProductionRun.id == run_id).first()
    if not db_run:
        raise HTTPException(status_code=404, detail="Production Run not found")
    
    update_data = run_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_run, key, value)
    
    db.commit()
    db.refresh(db_run)
    
    # Refresh item status
    refresh_item_status(db, db_run.item)
    
    return db_run

@router.delete("/{run_id}")
def delete_production_run(run_id: int, db: Session = Depends(get_db)):
    db_run = db.query(models.ProductionRun).filter(models.ProductionRun.id == run_id).first()
    if not db_run:
        raise HTTPException(status_code=404, detail="Production Run not found")
    
    item = db_run.item
    db.delete(db_run)
    db.commit()
    
    # Refresh item status
    if item:
        refresh_item_status(db, item)
        
    return {"message": "Production Run deleted successfully"}

# VIEW ROUTE
@router.get("/view", response_class=HTMLResponse)
def production_runs_view(request: Request, db: Session = Depends(get_db)):
    runs = db.query(models.ProductionRun).options(joinedload(models.ProductionRun.item)).all()
    return templates.TemplateResponse(
        "production_runs.html",
        {"request": request, "runs": runs}
    )
