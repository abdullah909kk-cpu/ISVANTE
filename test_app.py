import unittest
import json
from app import app
import database

class TestIsvanteApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_homepage(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"TIME, REDEFINED", res.data)
        self.assertIn(b"ISVANTE", res.data)

    def test_shop_page(self):
        res = self.client.get("/shop")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"All Watches", res.data)
        self.assertIn(b"Chrono Sovereign", res.data)

    def test_product_detail(self):
        res = self.client.get("/product/isvante-chrono-sovereign")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"ISVANTE Chrono Sovereign", res.data)
        self.assertIn(b"VK63", res.data)
        self.assertIn(b"Chat on WhatsApp", res.data)

    def test_cart_and_checkout_pages(self):
        res_cart = self.client.get("/cart")
        self.assertEqual(res_cart.status_code, 200)
        res_checkout = self.client.get("/checkout")
        self.assertEqual(res_checkout.status_code, 200)
        self.assertIn(b"Pakistan Checkout", res_checkout.data)

    def test_api_products(self):
        res = self.client.get("/api/products")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["products"]), 6)

    def test_api_ai_chat(self):
        res = self.client.post("/api/ai/chat", json={"message": "Do you deliver to Karachi via Cash on Delivery?"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertIn("Cash on Delivery", data["reply"])

    def test_place_real_order(self):
        order_payload = {
            "customer_name": "Hamza Test",
            "customer_phone": "03001234567",
            "customer_whatsapp": "03001234567",
            "customer_email": "hamza@example.com",
            "address": "House 10, Street 2, Sector F-6/1",
            "city": "Islamabad",
            "province": "Islamabad Capital Territory",
            "postal_code": "44000",
            "notes": "Please deliver in luxury box",
            "payment_method": "cod",
            "coupon_code": "ISVANTE10",
            "items": [
                {"id": 1, "quantity": 1}
            ]
        }
        res = self.client.post("/api/orders", json=order_payload)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        order_num = data["order"]["order_number"]
        self.assertTrue(order_num.startswith("ISV-"))

        # Verify tracking works
        track_res = self.client.get(f"/api/orders/track?order_number={order_num}&phone=03001234567")
        self.assertEqual(track_res.status_code, 200)
        track_data = json.loads(track_res.data)
        self.assertTrue(track_data["success"])
        self.assertEqual(track_data["order"]["customer_name"], "Hamza Test")

if __name__ == "__main__":
    unittest.main()
