import imaplib
import email
import re
from datetime import datetime, date
from sqlalchemy.orm import Session
from backend import models
from backend.utils import refresh_item_status

def sync_orders_from_gmail(db: Session):
    """
    Connects to Gmail via IMAP, searches for order emails,
    parses them, and saves to DemandOrder table.
    """
    settings = db.query(models.Settings).first()
    if not settings or not all([settings.sender_email, settings.app_password]):
        return {"status": "error", "message": "Gmail settings (email or app password) missing."}

    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(settings.sender_email, settings.app_password)
        mail.select("inbox")

        # Search for UNSEEN emails with subject "Demand Order"
        status, messages = mail.search(None, '(UNSEEN SUBJECT "Demand Order")')
        
        if status != "OK":
            return {"status": "error", "message": "Failed to search emails."}

        email_ids = messages[0].split()
        if not email_ids:
            return {"status": "success", "message": "No new demand order emails found.", "count": 0}

        orders_created = 0
        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            if status != "OK":
                continue

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()

                    # Parse body - Robust regex with optional colons
                    sku_match = re.search(r"SKU:?\s*([\w-]+)", body, re.IGNORECASE)
                    customer_match = re.search(r"Customer:?\s*(.*?)(?=\s*Quantity:?|Priority:?|Due Date:?|$)", body, re.IGNORECASE | re.DOTALL)
                    qty_match = re.search(r"Quantity:?\s*(\d+)", body, re.IGNORECASE)
                    date_match = re.search(r"Due Date:?\s*([\d-]+)", body, re.IGNORECASE)
                    priority_match = re.search(r"Priority:?\s*(HIGH|MEDIUM|LOW)", body, re.IGNORECASE)

                    if sku_match and customer_match and qty_match and date_match:
                        sku = sku_match.group(1).upper()
                        customer = customer_match.group(1).strip()
                        qty = int(qty_match.group(1))
                        due_date_str = date_match.group(1).strip()
                        
                        try:
                            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                        except ValueError:
                            continue

                        # Check if item exists
                        item = db.query(models.Item).filter(models.Item.sku == sku).first()
                        if not item:
                            continue

                        # Avoid duplicates in DB
                        existing = db.query(models.DemandOrder).filter(
                            models.DemandOrder.item_id == item.id,
                            models.DemandOrder.customer_name == customer,
                            models.DemandOrder.quantity == qty,
                            models.DemandOrder.due_date == due_date
                        ).first()

                        if not existing:
                            # Priority logic: parsed from email OR auto-calculated
                            if priority_match:
                                final_priority = priority_match.group(1).upper()
                            else:
                                from backend.routers.orders import calculate_priority
                                final_priority = calculate_priority(due_date)

                            new_order = models.DemandOrder(
                                item_id=item.id,
                                customer_name=customer,
                                quantity=qty,
                                due_date=due_date,
                                priority=final_priority,
                                status="OPEN"
                            )
                            
                            db.add(new_order)
                            refresh_item_status(db, item)
                            orders_created += 1

                            # Explicitly mark as Seen to prevent re-processing
                            mail.store(e_id, '+FLAGS', '\\Seen')

        db.commit()
        mail.logout()
        return {"status": "success", "message": f"Successfully pulled {orders_created} orders from Gmail.", "count": orders_created}

    except imaplib.IMAP4.error as e:
        error_msg = str(e)
        if "AUTHENTICATIONFAILED" in error_msg:
            return {"status": "error", "message": "Gmail Authentication Failed. Please check your App Password in Settings."}
        return {"status": "error", "message": f"IMAP Error: {error_msg}"}
    except Exception as e:
        print(f"Gmail sync error: {e}")
        return {"status": "error", "message": f"Failed to sync with Gmail: {str(e)}"}
