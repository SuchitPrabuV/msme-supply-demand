from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import pandas as pd

from backend.database import SessionLocal
from backend import models


router = APIRouter(prefix="/api", tags=["Ingestion"])
templates = Jinja2Templates(directory="frontend/templates")


# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/ingest")
async def ingest_csv(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        df = pd.read_csv(file.file)

        # Normalize headers
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(' ', '_')
            .str.replace('__', '_')
        )

    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV file")

    required_columns = [
        "sku",
        "name",
        "current_stock",
        "cost_price",
        "selling_price"
    ]

    # Validate required columns
    for col in required_columns:
        if col not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required column: {col}"
            )

    inserted_count = 0

    for _, row in df.iterrows():

        safety_stock = row.get("safety_stock", 0)
        min_order_qty = row.get("min_order_qty", 1)

        existing_item = db.query(models.Item).filter(
            models.Item.sku == row["sku"]
        ).first()

        if existing_item:
            continue

        new_item = models.Item(
            sku=row["sku"],
            name=row["name"],
            category=row.get("category"),
            current_stock=int(row["current_stock"]),
            cost_price=float(row["cost_price"]),
            selling_price=float(row["selling_price"]),
            safety_stock=int(safety_stock),
            min_order_qty=int(min_order_qty)
        )

        db.add(new_item)
        inserted_count += 1

    db.commit()

    # -------- PREVIEW LOGIC --------
    preview = df.head(5)
    preview_data = preview.to_dict(orient="records")

    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "preview_data": preview_data,
            "message": f"File processed successfully! {inserted_count} rows inserted."
        }
    )
