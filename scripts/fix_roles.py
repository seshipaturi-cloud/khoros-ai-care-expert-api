"""
Fix existing roles in the database to have all required fields
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from app.utils import connect_to_mongo, close_mongo_connection, get_database


async def fix_roles():
    """Fix existing roles to have all required fields"""
    await connect_to_mongo()
    db = get_database()
    
    print("Fixing existing roles...")
    
    # Define default values for missing fields
    defaults = {
        "is_system_role": False,
        "is_active": True,
        "can_be_delegated": False,
        "max_users": None,
        "brand_ids": None,
        "team_ids": None,
        "metadata": {},
        "description": ""
    }
    
    # Update all roles that are missing required fields
    async for role in db.roles.find():
        update_fields = {}
        
        for field, default_value in defaults.items():
            if field not in role:
                update_fields[field] = default_value
        
        # Ensure timestamps exist
        if "created_at" not in role:
            update_fields["created_at"] = datetime.utcnow()
        if "updated_at" not in role:
            update_fields["updated_at"] = datetime.utcnow()
        
        # Ensure role has proper structure
        if "name" not in role and "_id" in role:
            # If name is missing, use the _id as name
            update_fields["name"] = str(role["_id"])
        
        if "display_name" not in role:
            update_fields["display_name"] = role.get("name", "Unknown Role")
        
        if "role_type" not in role:
            # Try to infer from name
            name = role.get("name", "").lower()
            if "super" in name and "admin" in name:
                update_fields["role_type"] = "super_admin"
            elif "admin" in name:
                update_fields["role_type"] = "company_admin"
            elif "agent" in name:
                update_fields["role_type"] = "agent"
            else:
                update_fields["role_type"] = "custom"
        
        if "scope" not in role:
            # Try to infer from role_type
            role_type = role.get("role_type", update_fields.get("role_type", "custom"))
            if role_type == "super_admin":
                update_fields["scope"] = "system"
            elif role_type in ["company_admin", "analyst", "viewer"]:
                update_fields["scope"] = "company"
            elif role_type in ["brand_admin", "agent"]:
                update_fields["scope"] = "brand"
            elif role_type == "team_lead":
                update_fields["scope"] = "team"
            else:
                update_fields["scope"] = "company"
        
        if "permissions" not in role:
            update_fields["permissions"] = []
        
        if update_fields:
            print(f"Updating role {role.get('_id')} with fields: {list(update_fields.keys())}")
            await db.roles.update_one(
                {"_id": role["_id"]},
                {"$set": update_fields}
            )
    
    print("Role fixing completed!")
    
    # List all roles to verify
    print("\nCurrent roles in database:")
    async for role in db.roles.find():
        print(f"  - {role.get('name', 'unnamed')} ({role.get('role_type', 'unknown')})")
    
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(fix_roles())