"""
Migrate company IDs from strings to ObjectIds in MongoDB
This script will fix the issue where companies were created with string IDs instead of ObjectIds
"""

import asyncio
import sys
from pathlib import Path
from bson import ObjectId
from typing import Dict, Any

sys.path.append(str(Path(__file__).parent.parent))

from app.utils import connect_to_mongo, close_mongo_connection, get_database


async def migrate_company_ids():
    """Migrate company IDs from strings to ObjectIds"""
    await connect_to_mongo()
    db = get_database()
    
    print("Starting company ID migration...")
    print("-" * 50)
    
    # Get all companies
    companies = []
    async for company in db.companies.find():
        companies.append(company)
    
    print(f"Found {len(companies)} companies to check")
    
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    for company in companies:
        company_id = company.get('_id')
        company_name = company.get('name', 'Unknown')
        
        # Check if ID is already an ObjectId
        if isinstance(company_id, ObjectId):
            print(f"✓ {company_name}: Already using ObjectId")
            skipped_count += 1
            continue
        
        # If it's a string, we need to migrate it
        if isinstance(company_id, str):
            print(f"→ {company_name}: Migrating from string ID: {company_id}")
            
            try:
                # Create new ObjectId
                new_id = ObjectId()
                
                # Create new document with ObjectId
                new_company = company.copy()
                new_company['_id'] = new_id
                
                # Store the old string ID for reference
                new_company['old_string_id'] = company_id
                
                # Delete old document
                delete_result = await db.companies.delete_one({'_id': company_id})
                
                if delete_result.deleted_count == 0:
                    print(f"  ⚠ Failed to delete old document")
                    error_count += 1
                    continue
                
                # Insert new document with ObjectId
                await db.companies.insert_one(new_company)
                
                # Update all related collections
                # Update brands
                brands_updated = await db.brands.update_many(
                    {'company_id': company_id},
                    {'$set': {'company_id': str(new_id)}}
                )
                if brands_updated.modified_count > 0:
                    print(f"  → Updated {brands_updated.modified_count} brands")
                
                # Update ai_agents
                agents_updated = await db.ai_agents.update_many(
                    {'company_id': company_id},
                    {'$set': {'company_id': str(new_id)}}
                )
                if agents_updated.modified_count > 0:
                    print(f"  → Updated {agents_updated.modified_count} AI agents")
                
                # Update users
                users_updated = await db.users.update_many(
                    {'company_id': company_id},
                    {'$set': {'company_id': str(new_id)}}
                )
                if users_updated.modified_count > 0:
                    print(f"  → Updated {users_updated.modified_count} users")
                
                # Update knowledge_base_items
                kb_updated = await db.knowledge_base_items.update_many(
                    {'company_id': company_id},
                    {'$set': {'company_id': str(new_id)}}
                )
                if kb_updated.modified_count > 0:
                    print(f"  → Updated {kb_updated.modified_count} knowledge base items")
                
                print(f"  ✓ Successfully migrated to ObjectId: {new_id}")
                migrated_count += 1
                
            except Exception as e:
                print(f"  ✗ Error migrating {company_name}: {e}")
                error_count += 1
    
    print("\n" + "=" * 50)
    print("Migration Summary:")
    print(f"  Migrated: {migrated_count}")
    print(f"  Skipped (already ObjectId): {skipped_count}")
    print(f"  Errors: {error_count}")
    print("=" * 50)
    
    # Verify migration
    print("\nVerifying migration results...")
    async for company in db.companies.find():
        company_id = company.get('_id')
        company_name = company.get('name', 'Unknown')
        old_id = company.get('old_string_id', 'N/A')
        
        if isinstance(company_id, ObjectId):
            print(f"✓ {company_name}: ObjectId({company_id}) [old: {old_id}]")
        else:
            print(f"✗ {company_name}: Still using {type(company_id).__name__}: {company_id}")
    
    await close_mongo_connection()
    print("\nMigration complete!")


if __name__ == "__main__":
    asyncio.run(migrate_company_ids())