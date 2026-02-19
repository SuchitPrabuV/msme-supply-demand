from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models
from pydantic import BaseModel


router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])


class SupplierCreate(BaseModel):
    name: str
    contact_email: str | None = None
    lead_time_days: int = 7
    reliability_score: float = 1.0


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_supplier(data: SupplierCreate, db: Session = Depends(get_db)):

    supplier = models.Supplier(
        name=data.name,
        contact_email=data.contact_email,
        lead_time_days=data.lead_time_days,
        reliability_score=data.reliability_score
    )

    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    return supplier


@router.get("/")
def get_suppliers(db: Session = Depends(get_db)):
    return db.query(models.Supplier).all()
