import pandas as pd
import io
import os
import sys

# Mocking a subset of the logic from ingest.py to verify mapping
def verify_mapping():
    column_mapping = {
        "sku": ["sku", "item_code", "product_code", "id", "item_id", "part_number"],
        "name": ["name", "item_name", "product_name", "title", "description"],
        "current_stock": ["stock", "quantity", "qty", "current_stock", "on_hand", "stock_level"],
        "cost_price": ["cost", "cost_price", "purchase_price", "unit_cost", "buying_price"],
        "selling_price": ["selling_price", "price", "unit_price", "sale_price", "mrp"],
    }

    test_csv = io.StringIO("Item Code,Product Name,Qty,Unit Cost,MRP\nSKU001,Gadget,50,10.5,20.0")
    df = pd.read_csv(test_csv)
    
    # Normalize headers (as in ingest.py)
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    print(f"Normalized columns: {list(df.columns)}")

    rename_cfg = {}
    for internal_key, aliases in column_mapping.items():
        found = [col for col in df.columns if col in aliases]
        if found:
            rename_cfg[found[0]] = internal_key
    
    df = df.rename(columns=rename_cfg)
    
    print(f"Mapped columns: {list(df.columns)}")
    
    expected = ["sku", "name", "current_stock", "cost_price", "selling_price"]
    success = all(col in df.columns for col in expected)
    
    if success:
        print("✅ Mapping logic verified SUCCESSFUL!")
    else:
        print("❌ Mapping logic FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    verify_mapping()
