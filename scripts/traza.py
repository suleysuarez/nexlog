import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient('mongodb://localhost:27017')
db     = client['fintech_logs']

async def get_traza(correlation_id: str) -> dict:
    """
    Retrieves all logs from an operation given its correlation_id.
    Returns logs sorted chronologically (ASC).
    """
    cursor = db['logs'].find(
        {'correlation_id': correlation_id}
    ).sort('timestamp', 1)

    logs = await cursor.to_list(length=None)

    if not logs:
        raise ValueError(f'No logs found for correlation_id: {correlation_id}')

    for log in logs:
        log['_id'] = str(log['_id'])

    return {
        'correlation_id': correlation_id,
        'total_events':   len(logs),
        'types_present':  [log['type'] for log in logs],
        'flow':           logs
    }

async def main():
    # Test 1 — random correlation_id from database
    sample  = await db['logs'].find_one({}, {'correlation_id': 1, '_id': 0})
    corr_id = sample['correlation_id']

    print(f'Test 1 — random trace: {corr_id}')
    print('-' * 50)
    result = await get_traza(corr_id)
    print(f'Total events:  {result["total_events"]}')
    print(f'Types present: {result["types_present"]}')
    print('-' * 50)
    for log in result['flow']:
        print(f'{log["timestamp"]} | {log["type"]} | {log["service"]}')

    # Test 2 — complete trace with 4 events
    print('\nTest 2 — complete trace with 4 events: corr_nequi_cbe175b0c3fd4fb7')
    print('-' * 50)
    result2 = await get_traza('corr_nequi_cbe175b0c3fd4fb7')
    print(f'Total events:  {result2["total_events"]}')
    print(f'Types present: {result2["types_present"]}')
    print('-' * 50)
    for log in result2['flow']:
        print(f'{log["timestamp"]} | {log["type"]} | {log["service"]}')

    client.close()

asyncio.run(main())