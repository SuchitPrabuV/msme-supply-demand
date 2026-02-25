from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models, schemas

router = APIRouter(prefix="/api/settings", tags=["Settings"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=schemas.SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    settings = db.query(models.Settings).first()
    if not settings:
        # Initialize default settings if none exist
        settings = models.Settings(
            sender_email="",
            app_password="",
            recipient_email="",
            alerts_enabled=True
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.put("/", response_model=schemas.SettingsResponse)
def update_settings(settings_update: schemas.SettingsBase, db: Session = Depends(get_db)):
    db_settings = db.query(models.Settings).first()
    if not db_settings:
        db_settings = models.Settings()
        db.add(db_settings)

    update_data = settings_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_settings, key, value)
    
    db.commit()
    db.refresh(db_settings)
    return db_settings

@router.post("/test-email")
def test_email(db: Session = Depends(get_db)):
    from backend.email_service import send_critical_alert_email
    
    success = send_critical_alert_email(
        db, 
        item_id=0,
        item_name="[TEST ITEM]", 
        sku="TEST-000", 
        message="This is a test notification from your Pulse settings."
    )
    
    if success:
        return {"status": "success", "message": "Test email sent!"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test email. Check your SMTP settings and App Password.")
