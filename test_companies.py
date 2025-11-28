import requests

# Login first
login_response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={
        "email": "seshi.paturi@ignitetech.com",
        "password": "SuperAdmin123!"
    }
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"✅ Logged in successfully")
    
    # Test companies endpoint
    companies_response = requests.get(
        "http://localhost:8000/api/companies/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    
    print(f"\nCompanies API Response:")
    print(f"Status: {companies_response.status_code}")
    
    if companies_response.status_code == 200:
        data = companies_response.json()
        print(f"✅ Success! Found {data.get('total', 0)} companies")
        for company in data.get('companies', [])[:3]:
            print(f"  - {company.get('name')} ({company.get('status')})")
    else:
        print(f"❌ Error: {companies_response.text}")
else:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)