import asyncio
from app.utils import connect_to_mongo, close_mongo_connection, get_database

async def fix():
    await connect_to_mongo()
    db = get_database()
    result = await db.companies.update_many(
        {'plan': None},
        {'$set': {'plan': 'starter'}}
    )
    print(f'Updated {result.modified_count} companies with null plan to starter')
    await close_mongo_connection()

asyncio.run(fix())