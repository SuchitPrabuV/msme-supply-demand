import http.client
import json

conn = http.client.HTTPConnection("127.0.0.1", 8000)
payload = json.dumps({
  "sku": "ITEM100",
  "name": "Steel Rod",
  "category": "Metal",
  "cost_price": 50,
  "selling_price": 75,
  "current_stock": 100,
  "safety_stock": 20,
  "min_order_qty": 50
})
headers = {
  'Content-Type': 'application/json'
}
conn.request("POST", "/items/", payload, headers)
res = conn.getresponse()
data = res.read()
print(f"Status Code: {res.status}")
print("Response JSON:")
print(data.decode("utf-8"))
