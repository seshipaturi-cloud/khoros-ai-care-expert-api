import requests
import json
import time

# First login as super admin
login_response = requests.post(
    'http://localhost:8000/api/auth/login',
    json={'email': 'seshi.paturi@ignitetech.com', 'password': 'Pandu01#'}
)

if login_response.status_code != 200:
    print(f"Failed to login: {login_response.text}")
    exit(1)

token = login_response.json()['access_token']
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

print("✅ Logged in as super admin")

# Get all companies
companies_response = requests.get(
    'http://localhost:8000/api/companies/',
    headers=headers
)

if companies_response.status_code != 200:
    print(f"Failed to get companies: {companies_response.text}")
    exit(1)

companies = companies_response.json()['companies']
print(f"Found {len(companies)} companies")

# User templates
user_templates = {
    "company_admin": {
        "first_names": ["John", "Sarah", "Michael", "Emily", "David"],
        "last_names": ["Smith", "Johnson", "Williams", "Brown", "Davis"],
        "password": "Admin123!",
        "role": "company_admin"
    },
    "supervisors": {
        "first_names": ["Frank", "Grace"],
        "last_names": ["Garcia", "Hall"],
        "password": "Super123!",
        "role": "supervisor"
    },
    "agents": {
        "first_names": ["Alice", "Bob", "Carol", "Dan"],
        "last_names": ["Anderson", "Baker", "Clark", "Edwards"],
        "password": "Agent123!",
        "role": "agent"
    }
}

created_users = []

for idx, company in enumerate(companies):
    company_id = company['_id']
    company_name = company['name']
    print(f"\n{idx + 1}. Creating users for company: {company_name}")
    
    # Create company admin
    admin = user_templates["company_admin"]
    admin_first = admin["first_names"][idx % len(admin["first_names"])]
    admin_last = admin["last_names"][idx % len(admin["last_names"])]
    admin_email = f"{admin_first.lower()}.{admin_last.lower()}@{company_name.lower().replace(' ', '').replace('-', '')}.com"
    
    admin_data = {
        "email": admin_email,
        "username": f"{admin_first.lower()}{admin_last.lower()[0]}",
        "password": admin["password"],
        "full_name": f"{admin_first} {admin_last}",
        "role": admin["role"],
        "company_id": company_id,
        "is_active": True
    }
    
    # Register the company admin
    register_response = requests.post(
        'http://localhost:8000/api/auth/register',
        headers=headers,
        json=admin_data
    )
    
    if register_response.status_code in [200, 201]:
        print(f"  ✅ Created company_admin: {admin_email} (Password: {admin['password']})")
        created_users.append(admin_data)
    elif register_response.status_code == 400:
        print(f"  ⚠️  Company admin already exists: {admin_email}")
    else:
        print(f"  ❌ Failed to create company_admin: {register_response.text}")
    
    # Create supervisor
    supervisor = user_templates["supervisors"]
    sup_idx = idx % len(supervisor["first_names"])
    sup_first = supervisor["first_names"][sup_idx]
    sup_last = supervisor["last_names"][sup_idx]
    sup_email = f"{sup_first.lower()}.{sup_last.lower()}@{company_name.lower().replace(' ', '').replace('-', '')}.com"
    
    sup_data = {
        "email": sup_email,
        "username": f"{sup_first.lower()}{sup_last.lower()[0]}",
        "password": supervisor["password"],
        "full_name": f"{sup_first} {sup_last}",
        "role": supervisor["role"],
        "company_id": company_id,
        "is_active": True
    }
    
    register_response = requests.post(
        'http://localhost:8000/api/auth/register',
        headers=headers,
        json=sup_data
    )
    
    if register_response.status_code in [200, 201]:
        print(f"  ✅ Created supervisor: {sup_email} (Password: {supervisor['password']})")
        created_users.append(sup_data)
    elif register_response.status_code == 400:
        print(f"  ⚠️  Supervisor already exists: {sup_email}")
    else:
        print(f"  ❌ Failed to create supervisor: {register_response.text}")
    
    # Create 2 agents
    agents = user_templates["agents"]
    for agent_num in range(2):
        agent_idx = (idx * 2 + agent_num) % len(agents["first_names"])
        agent_first = agents["first_names"][agent_idx]
        agent_last = agents["last_names"][agent_idx]
        agent_email = f"{agent_first.lower()}.{agent_last.lower()}{agent_num+1}@{company_name.lower().replace(' ', '').replace('-', '')}.com"
        
        agent_data = {
            "email": agent_email,
            "username": f"{agent_first.lower()}{agent_last.lower()[0]}{agent_num+1}",
            "password": agents["password"],
            "full_name": f"{agent_first} {agent_last}",
            "role": agents["role"],
            "company_id": company_id,
            "is_active": True
        }
        
        register_response = requests.post(
            'http://localhost:8000/api/auth/register',
            headers=headers,
            json=agent_data
        )
        
        if register_response.status_code in [200, 201]:
            print(f"  ✅ Created agent: {agent_email} (Password: {agents['password']})")
            created_users.append(agent_data)
        elif register_response.status_code == 400:
            print(f"  ⚠️  Agent already exists: {agent_email}")
        else:
            print(f"  ❌ Failed to create agent: {register_response.text}")
    
    # Small delay to avoid overwhelming the server
    time.sleep(0.5)

# Print summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

# Get updated user count
users_response = requests.get(
    'http://localhost:8000/api/users/',
    headers=headers
)

if users_response.status_code == 200:
    total_users = users_response.json()['total']
    print(f"Total users in system: {total_users}")
    
    users = users_response.json()['users']
    
    # Count by role
    role_counts = {}
    for user in users:
        role = user.get('role', 'unknown')
        role_counts[role] = role_counts.get(role, 0) + 1
    
    print("\nUsers by role:")
    for role, count in sorted(role_counts.items()):
        print(f"  {role}: {count}")
    
    # Count by company
    company_counts = {}
    for user in users:
        company_name = user.get('company_name', 'No Company')
        if not company_name:
            company_name = 'No Company'
        company_counts[company_name] = company_counts.get(company_name, 0) + 1
    
    print("\nUsers by company:")
    for company_name, count in sorted(company_counts.items()):
        print(f"  {company_name}: {count}")

print("\n" + "=" * 70)
print("LOGIN CREDENTIALS")
print("=" * 70)
print("Super Admin:")
print("  Email: seshi.paturi@ignitetech.com")
print("  Password: Pandu01#")
print("\nCompany Admins:")
print("  Password: Admin123!")
print("\nSupervisors:")
print("  Password: Super123!")
print("\nAgents:")
print("  Password: Agent123!")
print("\n" + "=" * 70)

if created_users:
    print("\nNewly created users:")
    for user in created_users[:5]:  # Show first 5
        print(f"  {user['email']} ({user['role']})")
    if len(created_users) > 5:
        print(f"  ... and {len(created_users) - 5} more")