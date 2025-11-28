import requests

# Login
r = requests.post('http://localhost:8000/api/auth/login', 
                  json={'email':'seshi.paturi@ignitetech.com','password':'SuperAdmin123!'})

if r.status_code == 200:
    token = r.json()['access_token']
    print("✅ Logged in")
    
    # Try to delete
    company_id = '68c670ab9b7f339e05962db4'  # HealthPlus Medical
    response = requests.delete(
        f'http://localhost:8000/api/companies/{company_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    print(f'\nDelete Company Response:')
    print(f'Status: {response.status_code}')
    if response.status_code != 204:
        print(f'Response: {response.text}')
else:
    print(f"Login failed: {r.text}")