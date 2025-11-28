import requests

response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={
        "email": "seshi.paturi@ignitetech.com",
        "password": "SuperAdmin123!"
    }
)

if response.status_code == 200:
    print("✅ Login successful!")
    data = response.json()
    print(f"Token (first 50 chars): {data['access_token'][:50]}...")
else:
    print(f"❌ Login failed: {response.status_code}")
    print(f"Response: {response.text}")