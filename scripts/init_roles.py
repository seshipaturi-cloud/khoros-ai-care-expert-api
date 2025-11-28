"""
Initialize default roles in the database
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from app.utils import connect_to_mongo, close_mongo_connection, get_database
from app.models.role import ROLE_TEMPLATES, RoleType


async def init_roles():
    """Initialize default system roles"""
    await connect_to_mongo()
    db = get_database()
    
    print("Initializing default roles...")
    
    for role_type, template in ROLE_TEMPLATES.items():
        role_name = role_type.value
        
        existing_role = await db.roles.find_one({
            "name": role_name,
            "is_system_role": True
        })
        
        if existing_role:
            print(f"Role '{role_name}' already exists, skipping...")
            continue
        
        role_data = {
            "name": role_name,
            "display_name": template["display_name"],
            "role_type": role_type.value,
            "scope": template["scope"].value,
            "permissions": [p.value if hasattr(p, 'value') else p for p in template["permissions"]],
            "is_system_role": template.get("is_system_role", True),
            "is_active": True,
            "can_be_delegated": False,
            "description": template.get("description", ""),
            "company_id": None,
            "brand_ids": None,
            "team_ids": None,
            "max_users": None,
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "system",
            "updated_by": "system"
        }
        
        result = await db.roles.insert_one(role_data)
        print(f"Created role '{role_name}' with ID: {result.inserted_id}")
    
    await close_mongo_connection()
    print("Role initialization completed!")


if __name__ == "__main__":
    asyncio.run(init_roles())