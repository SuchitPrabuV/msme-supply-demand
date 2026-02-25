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
