import json
import aiohttp
import asyncio
from decouple import config
token = config('TOKEN')

async def fetch_graphql(session, url, query, variables, token):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    payload = {
        'query': query,
        'variables': variables,
    }

    attempt = 0
    while True:  # Infinite retry loop
        try:
            async with session.post(url, headers=headers, data=json.dumps(payload)) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'errors' in data:
                        print(f"GraphQL errors: {data['errors']}")
                        return None
                    return data
                else:
                    print(f"Request failed with status {response.status}")
        except aiohttp.ClientError as e:
            print(f"Request exception: {e}")

        # Exponential backoff and retry
        attempt += 1
        wait_time = min(5 * 2 ** attempt, 30)  # Exponential backoff with max wait time of 30 seconds
        print(f"Retrying in {wait_time} seconds (attempt {attempt})...")
        await asyncio.sleep(wait_time)