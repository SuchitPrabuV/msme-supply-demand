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


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Check if any items are using this supplier
    item_count = db.query(models.Item).filter(models.Item.supplier_id == supplier_id).count()
    if item_count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete supplier: {item_count} items are linked to it.")

    db.delete(supplier)
    db.commit()
    return {"message": "Supplier deleted successfully"}
