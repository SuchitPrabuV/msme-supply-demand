import http.client
import mimetypes

conn = http.client.HTTPConnection("127.0.0.1", 8000)
file_path = "test_inventory.csv"
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'

with open(file_path, "rb") as f:
    file_content = f.read()

body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="{file_path}"\r\n'
    f'Content-Type: text/csv\r\n\r\n'
).encode() + file_content + f'\r\n--{boundary}--\r\n'.encode()

headers = {
    'Content-Type': f'multipart/form-data; boundary={boundary}',
    'Content-Length': str(len(body))
}

conn.request("POST", "/api/ingest", body, headers)
res = conn.getresponse()
data = res.read()

print(f"Status Code: {res.status}")
print("Response JSON:")
print(data.decode("utf-8"))
