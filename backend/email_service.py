import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from backend import models

def send_critical_alert_email(db: Session, item_id: int, item_name: str, sku: str, message: str):
    """
    Fetches settings and latest recommendation, then sends a critical alert email.
    """
    settings = db.query(models.Settings).first()
    
    if not settings or not settings.alerts_enabled:
        return False
    
    if not all([settings.sender_email, settings.app_password, settings.recipient_email]):
        print("Gmail settings incomplete. Skipping email.")
        return False

    # Fetch latest recommendation for this item
    rec = db.query(models.Recommendation).filter(
        models.Recommendation.item_id == item_id,
        models.Recommendation.status == "PENDING"
    ).order_by(models.Recommendation.created_at.desc()).first()

    recommendation_html = ""
    if rec:
        recommendation_html = f"""
        <div style="margin-top: 15px; padding: 12px; border-left: 4px solid #17a2b8; background-color: #e3f2fd;">
            <p style="margin: 0; color: #0c5460; font-weight: bold;">Quick Fix Recommendation:</p>
            <p style="margin: 5px 0 0 0; font-style: italic;">{rec.rationale}</p>
            {f'<p style="margin: 5px 0 0 0;"><strong>Recommended Quantity:</strong> {rec.recommended_qty} units</p>' if rec.recommended_qty and rec.recommended_qty > 0 else ''}
        </div>
        """

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.sender_email
        msg['To'] = settings.recipient_email
        msg['Subject'] = f"CRITICAL STOCK ALERT: {sku} - {item_name}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #dc3545; border-bottom: 2px solid #dc3545; padding-bottom: 10px;">Critical Inventory Alert</h2>
            <p>The control tower has detected a critical risk for <strong>{item_name}</strong> ({sku}).</p>
            <div style="background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; border: 1px solid #f5c6cb;">
                <strong>Alert Details:</strong> {message}
            </div>
            
            {recommendation_html}

            <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;">
                <p style="font-size: 0.9em; color: #666;">
                    This is an automated notification from your <strong>Pulse</strong> Control Tower.<br>
                    Please log in to the dashboard to take corrective action.
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        # Connect and send
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(settings.sender_email, settings.app_password)
            server.send_message(msg)
            
        print(f"Alert email sent for {sku}")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_po_email(db: Session, supply_order_id: int):
    """
    Sends a professional Purchase Order email to the supplier.
    """
    order = db.query(models.SupplyOrder).filter(models.SupplyOrder.id == supply_order_id).first()
    if not order or not order.item:
        return False

    # Try to find the supplier linked to the item or by name
    supplier = order.item.supplier
    if not supplier:
        # Fallback to searching by name if the link is missing
        supplier = db.query(models.Supplier).filter(models.Supplier.name == order.supplier_name).first()

    if not supplier or not supplier.contact_email:
        print(f"No contact email for supplier: {order.supplier_name}. Skipping PO email.")
        return False

    settings = db.query(models.Settings).first()
    if not settings or not settings.sender_email or not settings.app_password:
        print("Gmail settings incomplete. Skipping PO email.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = settings.sender_email
        msg['To'] = supplier.contact_email
        msg['Subject'] = f"PURCHASE ORDER: PO-{order.id} for {order.item.sku}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px;">
                <h2 style="color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 10px;">Purchase Order</h2>
                <p>Dear <strong>{supplier.name}</strong>,</p>
                <p>Please find the details for our recent purchase order:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 10px; border: 1px solid #dee2e6; text-align: left;">PO Number</th>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">PO-{order.id}</td>
                    </tr>
                    <tr>
                        <th style="padding: 10px; border: 1px solid #dee2e6; text-align: left;">Item</th>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{order.item.name} ({order.item.sku})</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 10px; border: 1px solid #dee2e6; text-align: left;">Quantity</th>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>{order.quantity} units</strong></td>
                    </tr>
                    <tr>
                        <th style="padding: 10px; border: 1px solid #dee2e6; text-align: left;">Order Date</th>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{order.order_date.strftime('%d-%m-%Y')}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 10px; border: 1px solid #dee2e6; text-align: left;">Expected Delivery</th>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{order.expected_delivery_date.strftime('%d-%m-%Y')}</td>
                    </tr>
                </table>

                <p style="margin-top: 20px;">Please confirm receipt of this order and the expected delivery date.</p>
                
                <div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #eee; font-size: 0.85em; color: #777;">
                    <p>Sent via <strong>Pulse MSME Control Tower</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(settings.sender_email, settings.app_password)
            server.send_message(msg)
            
        print(f"PO email sent to {supplier.name} ({supplier.contact_email})")
        return True
        
    except Exception as e:
        print(f"Failed to send PO email: {e}")
        return False
