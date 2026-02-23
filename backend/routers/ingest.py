from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import pandas as pd
import os
from datetime import datetime
from backend.database import SessionLocal
from backend import models
from backend.engine import calculate_projection
from backend.alert_engine import run_alert_engine


router = APIRouter(prefix="/api", tags=["Ingestion"])
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "frontend", "templates"))


# ---------------- DB Dependency ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- INGEST CSV ----------------
@router.post("/ingest")
async def ingest_csv(
    request: Request,
    file_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        df = pd.read_csv(file.file)
        
        # Normalize headers
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

    except Exception as e:
        print(f"DEBUG: CSV Read Error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid CSV file: {str(e)}")

    print(f"DEBUG: Processing file_type='{file_type}' with raw columns: {list(df.columns)}")

    # Dynamic Column Mapping
    column_mapping = {
        "sku": ["sku", "item_code", "product_code", "id", "item_id", "part_number"],
        "name": ["name", "item_name", "product_name", "title", "description"],
        "quantity": ["quantity", "qty", "amount", "vol", "current_stock", "stock", "on_hand", "stock_level"],
        "cost_price": ["cost", "cost_price", "purchase_price", "unit_cost", "buying_price"],
        "selling_price": ["selling_price", "price", "unit_price", "sale_price", "mrp"],
        "safety_stock": ["safety", "safety_stock", "min_stock", "buffer_stock"],
        "min_order_qty": ["moq", "min_order_qty", "order_multiple"],
        "customer_name": ["customer", "client", "customer_name", "buyer"],
        "supplier_name": ["supplier", "vendor", "supplier_name", "source"],
        "due_date": ["due_date", "promise_date", "finish_date", "delivery_date"],
        "order_date": ["order_date", "purchase_date", "date"],
        "expected_delivery_date": ["expected_delivery", "expected_delivery_date", "arrival_date"],
        "start_date": ["start_date", "begin_date", "commencement_date"],
        "end_date": ["end_date", "finish_date", "completion_date"],
        "priority": ["priority", "importance", "status_level"]
    }

    # Apply mapping: rename found aliases to internal keys
    rename_cfg = {}
    for internal_key, aliases in column_mapping.items():
        found = [col for col in df.columns if col in aliases]
        if found:
            rename_cfg[found[0]] = internal_key
    
    df = df.rename(columns=rename_cfg)
    print(f"DEBUG: Final mapped columns: {list(df.columns)}")

    # Route to correct handler
    try:
        if file_type == "items":
            inserted_count = handle_items(df, db)
        elif file_type == "demand_orders":
            inserted_count = handle_demand_orders(df, db)
        elif file_type == "supply_orders":
            inserted_count = handle_supply_orders(df, db)
        elif file_type == "production_runs":
            inserted_count = handle_production_runs(df, db)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid file_type: {file_type}")
    except HTTPException as he:
        # Re-raise to provide better context if it's our error
        raise he
    except Exception as e:
        print(f"DEBUG: Handler error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal handler error: {str(e)}")

    db.commit()

    # Post-ingestion logic: Refresh all alerts and recommendations
    items = db.query(models.Item).all()
    from backend.utils import refresh_item_status
    for item in items:
        refresh_item_status(db, item)

    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "message": f"Successfully ingested {inserted_count} rows into {file_type}.",
            "preview_data": None
        }
    )

def handle_items(df, db):
    required = ["sku", "name", "quantity", "cost_price", "selling_price"]

    for col in required:
        if col not in df.columns:
            msg = f"Missing column for Item upload: '{col}'. Found: {list(df.columns)}"
            print(f"DEBUG Error: {msg}")
            raise HTTPException(status_code=400, detail=msg)

    count = 0

    for _, row in df.iterrows():

        if row["cost_price"] < 0 or row["selling_price"] < 0:
            raise HTTPException(status_code=400, detail="Price cannot be negative")

        existing = db.query(models.Item).filter(
            models.Item.sku == str(row["sku"]).upper()
        ).first()

        if existing:
            # Update existing item instead of skipping
            existing.current_stock = int(row["quantity"])
            existing.cost_price = float(row["cost_price"])
            existing.selling_price = float(row["selling_price"])
            existing.safety_stock = int(row.get("safety_stock", 0))
            existing.min_order_qty = int(row.get("min_order_qty", 1))
            count += 1
            continue

        item = models.Item(
            sku=str(row["sku"]).upper(),
            name=row["name"],
            category=row.get("category"),
            current_stock=int(row["quantity"]),
            cost_price=float(row["cost_price"]),
            selling_price=float(row["selling_price"]),
            safety_stock=int(row.get("safety_stock", 0)),
            min_order_qty=int(row.get("min_order_qty", 1)),
        )

        db.add(item)
        count += 1

    return count




def handle_demand_orders(df, db):
    required = ["sku", "customer_name", "quantity", "due_date", "priority"]

    for col in required:
        if col not in df.columns:
            msg = f"Missing column for Demand Order upload: '{col}'. Found: {list(df.columns)}"
            print(f"DEBUG Error: {msg}")
            raise HTTPException(status_code=400, detail=msg)

    count = 0

    for _, row in df.iterrows():

        item = db.query(models.Item).filter(
            models.Item.sku == str(row["sku"]).upper()
        ).first()

        if not item:
            raise HTTPException(status_code=400, detail=f"SKU not found: {row['sku']}")

        if row["priority"] not in ["LOW", "MEDIUM", "HIGH"]:
            raise HTTPException(status_code=400, detail="Invalid priority")

        # Flexible date parsing
        due_date = pd.to_datetime(row["due_date"]).date()

        order = models.DemandOrder(
            item_id=item.id,
            customer_name=row["customer_name"],
            quantity=int(row["quantity"]),
            due_date=due_date,
            priority=row["priority"],
            status="OPEN"
        )

        db.add(order)
        count += 1

    return count


def handle_supply_orders(df, db):
    required = ["sku", "supplier_name", "quantity", "order_date", "expected_delivery_date"]

    for col in required:
        if col not in df.columns:
            msg = f"Missing column for Supply Order upload: '{col}'. Found: {list(df.columns)}"
            print(f"DEBUG Error: {msg}")
            raise HTTPException(status_code=400, detail=msg)

    count = 0

    for _, row in df.iterrows():

        item = db.query(models.Item).filter(
            models.Item.sku == str(row["sku"]).upper()
        ).first()

        if not item:
            raise HTTPException(status_code=400, detail=f"SKU not found: {row['sku']}")

        # Flexible date parsing
        order_date = pd.to_datetime(row["order_date"]).date()
        delivery_date = pd.to_datetime(row["expected_delivery_date"]).date()

        order = models.SupplyOrder(
            item_id=item.id,
            supplier_name=str(row["supplier_name"]),
            quantity=int(row["quantity"]),
            order_date=order_date,
            expected_delivery_date=delivery_date,
            status="ORDERED"
        )
        

        db.add(order)
        count += 1

    return count

def handle_production_runs(df, db):
    required = ["sku", "quantity", "start_date", "end_date"]

    for col in required:
        if col not in df.columns:
            msg = f"Missing column for Production Run upload: '{col}'. Found: {list(df.columns)}"
            print(f"DEBUG Error: {msg}")
            raise HTTPException(status_code=400, detail=msg)

    count = 0

    for _, row in df.iterrows():

        item = db.query(models.Item).filter(
            models.Item.sku == str(row["sku"]).upper()
        ).first()

        if not item:
            raise HTTPException(status_code=400, detail=f"SKU not found: {row['sku']}")

        # Flexible date parsing
        start_date = pd.to_datetime(row["start_date"]).date()
        end_date = pd.to_datetime(row["end_date"]).date()

        prod_run = models.ProductionRun(
            item_id=item.id,
            quantity=int(row["quantity"]),
            start_date=start_date,
            end_date=end_date,
            status="PLANNED"
        )

        db.add(prod_run)
        count += 1

    return count
