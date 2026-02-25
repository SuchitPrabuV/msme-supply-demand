import unittest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from backend import models, gmail_service
from backend.database import SessionLocal, engine
from datetime import date

class TestGmailSync(unittest.TestCase):
    def setUp(self):
        # Ensure we have a clean test environment
        models.Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        
        # Setup test item
        self.test_sku = "SYNC-TEST-01"
        item = self.db.query(models.Item).filter(models.Item.sku == self.test_sku).first()
        if item:
            self.db.delete(item)
            self.db.commit()
        
        self.item = models.Item(
            sku=self.test_sku,
            name="Gmail Sync Test Item",
            current_stock=100,
            cost_price=10.0,
            selling_price=20.0
        )
        self.db.add(self.item)
        
        # Setup settings
        settings = self.db.query(models.Settings).first()
        if not settings:
            settings = models.Settings(sender_email="test@gmail.com", app_password="password")
            self.db.add(settings)
        else:
            settings.sender_email = "test@gmail.com"
            settings.app_password = "password"
        
        self.db.commit()

    def tearDown(self):
        self.db.query(models.DemandOrder).filter(models.DemandOrder.item_id == self.item.id).delete()
        self.db.delete(self.item)
        self.db.commit()
        self.db.close()

    @patch("imaplib.IMAP4_SSL")
    def test_sync_logic(self, mock_imap):
        # Setup Mock IMAP
        instance = mock_imap.return_value
        instance.login.return_value = "OK"
        instance.select.return_value = "OK"
        instance.search.return_value = ("OK", [b"1 2"])
        
        # Mock fetch results for two emails
        email_body_1 = f"SKU: {self.test_sku}\nCustomer: Alice\nQuantity: 25\nDue Date: 2026-05-01".encode()
        email_body_2 = f"SKU: {self.test_sku}\nCustomer: Bob\nQuantity: 30\nDue Date: 2026-05-02".encode()
        
        msg1 = MagicMock()
        msg1.is_multipart.return_value = False
        msg1.get_payload.return_value = email_body_1
        
        msg2 = MagicMock()
        msg2.is_multipart.return_value = False
        msg2.get_payload.return_value = email_body_2

        # Mock imap response structure
        # (status, [(None, RFC822_DATA)])
        instance.fetch.side_effect = [
            ("OK", [(None, b"Header\r\n\r\n" + email_body_1)]),
            ("OK", [(None, b"Header\r\n\r\n" + email_body_2)])
        ]

        # Patch email.message_from_bytes to return our mocked messages
        with patch("email.message_from_bytes") as mock_msg_from_bytes:
            mock_msg_from_bytes.side_effect = [msg1, msg2]
            
            print("Running sync_orders_from_gmail...")
            result = gmail_service.sync_orders_from_gmail(self.db)
            
            print(f"Result: {result}")
            self.assertEqual(result["count"], 2)
            
            # Verify orders in DB
            orders = self.db.query(models.DemandOrder).filter(models.DemandOrder.item_id == self.item.id).all()
            self.assertEqual(len(orders), 2)
            
            order_customers = [o.customer_name for o in orders]
            self.assertIn("Alice", order_customers)
            self.assertIn("Bob", order_customers)
            
            print("SUCCESS: Sync logic verified with mocks!")

    @patch("imaplib.IMAP4_SSL")
    def test_sync_logic_single_line(self, mock_imap):
        # Setup Mock IMAP
        instance = mock_imap.return_value
        instance.login.return_value = "OK"
        instance.select.return_value = "OK"
        instance.search.return_value = ("OK", [b"1"])
        
        # Single line format
        email_body = f"SKU: {self.test_sku} Customer: Charlie Quantity: 15 Due Date: 2026-05-05".encode()
        
        msg = MagicMock()
        msg.is_multipart.return_value = False
        msg.get_payload.return_value = email_body

        instance.fetch.side_effect = [
            ("OK", [(None, b"Header\r\n\r\n" + email_body)])
        ]

        with patch("email.message_from_bytes") as mock_msg_from_bytes:
            mock_msg_from_bytes.side_effect = [msg]
            
            print("Running sync_orders_from_gmail (single line)...")
            result = gmail_service.sync_orders_from_gmail(self.db)
            
            print(f"Result: {result}")
            self.assertEqual(result["count"], 1)
            
            order = self.db.query(models.DemandOrder).filter(
                models.DemandOrder.item_id == self.item.id,
                models.DemandOrder.customer_name == "Charlie"
            ).first()
            self.assertIsNotNone(order)
            self.assertEqual(order.quantity, 15)
            
            print("SUCCESS: Single-line sync logic verified!")

    @patch("imaplib.IMAP4_SSL")
    def test_sync_logic_priority(self, mock_imap):
        # Setup Mock IMAP
        instance = mock_imap.return_value
        instance.login.return_value = "OK"
        instance.select.return_value = "OK"
        instance.search.return_value = ("OK", [b"1"])
        
        # Email with explicit HIGH priority
        email_body = f"SKU: {self.test_sku} Customer: Dave Quantity: 10 Due Date: 2026-06-01 Priority: HIGH".encode()
        
        msg = MagicMock()
        msg.is_multipart.return_value = False
        msg.get_payload.return_value = email_body

        instance.fetch.side_effect = [
            ("OK", [(None, b"Header\r\n\r\n" + email_body)])
        ]

        with patch("email.message_from_bytes") as mock_msg_from_bytes:
            mock_msg_from_bytes.side_effect = [msg]
            
            print("Running sync_orders_from_gmail (explicit priority)...")
            result = gmail_service.sync_orders_from_gmail(self.db)
            
            self.assertEqual(result["count"], 1)
            order = self.db.query(models.DemandOrder).filter(models.DemandOrder.customer_name == "Dave").first()
            self.assertEqual(order.priority, "HIGH")
            print("SUCCESS: Explicit priority verified!")

            self.assertEqual(order.priority, "HIGH")
            print("SUCCESS: Explicit priority verified!")

    @patch("imaplib.IMAP4_SSL")
    def test_sync_logic_no_colons(self, mock_imap):
        # Setup Mock IMAP
        instance = mock_imap.return_value
        instance.login.return_value = "OK"
        instance.select.return_value = "OK"
        instance.search.return_value = ("OK", [b"1"])
        
        # Format without colons
        email_body = f"SKU {self.test_sku} Customer John Doe Quantity 50 Due Date 2026-03-10".encode()
        
        msg = MagicMock()
        msg.is_multipart.return_value = False
        msg.get_payload.return_value = email_body

        instance.fetch.side_effect = [
            ("OK", [(None, b"Header\r\n\r\n" + email_body)])
        ]

        with patch("email.message_from_bytes") as mock_msg_from_bytes:
            mock_msg_from_bytes.side_effect = [msg]
            
            print("Running sync_orders_from_gmail (no colons)...")
            result = gmail_service.sync_orders_from_gmail(self.db)
            
            self.assertEqual(result["count"], 1)
            # Verify Seen flag was stored
            instance.store.assert_called_with(b"1", '+FLAGS', '\\Seen')
            print("SUCCESS: No-colon format and Seen flag verified!")

if __name__ == "__main__":
    unittest.main()
