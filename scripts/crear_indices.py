import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING

client = AsyncIOMotorClient('mongodb://localhost:27017')
db     = client['fintech_logs']

async def create_indexes():
    col = db['logs']

    await col.create_index(
        [('timestamp', DESCENDING)],
        name='idx_timestamp_desc'
    )
    print('1/7 - idx_timestamp_desc created')

    await col.create_index(
        [('type', ASCENDING)],
        name='idx_type'
    )
    print('2/7 - idx_type created')

    await col.create_index(
        [('service', ASCENDING)],
        name='idx_service'
    )
    print('3/7 - idx_service created')

    await col.create_index(
        [('user_id', ASCENDING)],
        name='idx_user_id'
    )
    print('4/7 - idx_user_id created')

    await col.create_index(
        [('correlation_id', ASCENDING)],
        name='idx_correlation_id'
    )
    print('5/7 - idx_correlation_id created')

    await col.create_index(
        [('expires_at', ASCENDING)],
        expireAfterSeconds=0,
        name='idx_ttl_expires_at'
    )
    print('6/7 - idx_ttl_expires_at (TTL) created')

    await col.create_index(
        [('type', ASCENDING), ('timestamp', DESCENDING)],
        name='idx_type_timestamp'
    )
    print('7/7 - idx_type_timestamp (compound) created')

    print('\nAll indexes created successfully')
    client.close()

asyncio.run(create_indexes())