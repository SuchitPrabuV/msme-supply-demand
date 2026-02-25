from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import gmail_service

router = APIRouter(prefix="/api/gmail", tags=["Gmail"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/sync")
def sync_gmail(db: Session = Depends(get_db)):
    """
    Endpoint to trigger manual sync of demand orders from Gmail.
    """
    result = gmail_service.sync_orders_from_gmail(db)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result
