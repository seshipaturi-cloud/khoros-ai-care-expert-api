"""
Fix company plan values in database
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.utils import connect_to_mongo, close_mongo_connection, get_database


async def fix_company_plans():
    """Fix company plan values to be lowercase"""
    await connect_to_mongo()
    db = get_database()
    
    print("Fixing company plan values...")
    
    # Update all companies with uppercase plans to lowercase
    plan_map = {
        'STARTER': 'starter',
        'PROFESSIONAL': 'professional',
        'ENTERPRISE': 'enterprise',
        'CUSTOM': 'custom'
    }
    
    for old_plan, new_plan in plan_map.items():
        result = await db.companies.update_many(
            {"plan": old_plan},
            {"$set": {"plan": new_plan}}
        )
        if result.modified_count > 0:
            print(f"Updated {result.modified_count} companies from {old_plan} to {new_plan}")
    
    # Also fix status values if needed
    status_map = {
        'ACTIVE': 'active',
        'SUSPENDED': 'suspended',
        'TRIAL': 'trial',
        'EXPIRED': 'expired'
    }
    
    for old_status, new_status in status_map.items():
        result = await db.companies.update_many(
            {"status": old_status},
            {"$set": {"status": new_status}}
        )
        if result.modified_count > 0:
            print(f"Updated {result.modified_count} companies from {old_status} to {new_status}")
    
    # List all companies to verify
    print("\nCurrent companies:")
    async for company in db.companies.find():
        print(f"  - {company.get('name')}: plan={company.get('plan')}, status={company.get('status')}")
    
    await close_mongo_connection()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(fix_company_plans())