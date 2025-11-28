import asyncio
from bson import ObjectId
from app.utils import connect_to_mongo, close_mongo_connection, get_database
from app.services.company_service import company_service

async def test_delete():
    await connect_to_mongo()
    db = get_database()
    
    company_id = '68c670ab9b7f339e05962db4'  # HealthPlus Medical
    
    # Check if company exists
    company = await db.companies.find_one({"_id": ObjectId(company_id)})
    if company:
        print(f"✅ Company found: {company.get('name')}")
    else:
        print(f"❌ Company not found with ID: {company_id}")
        await close_mongo_connection()
        return
    
    # Check for brands
    brands_count = await db.brands.count_documents({"company_id": company_id})
    print(f"   Brands count: {brands_count}")
    
    # Try to delete
    try:
        result = await company_service.delete_company(company_id)
        print(f"   Delete result: {result}")
        
        # Check if company still exists
        company_after = await db.companies.find_one({"_id": ObjectId(company_id)})
        if company_after:
            print(f"   Company still exists with status: {company_after.get('status')}")
        else:
            print(f"   Company deleted successfully")
    except Exception as e:
        print(f"❌ Error deleting: {e}")
    
    await close_mongo_connection()

asyncio.run(test_delete())