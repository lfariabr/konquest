import json
import aiohttp
import asyncio
import logging
from decouple import config

logger = logging.getLogger(__name__)
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
    max_attempts = 3
    
    while attempt < max_attempts:
        try:
            async with session.post(url, headers=headers, data=json.dumps(payload)) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'errors' in data:
                        error_msg = data['errors'][0].get('message', 'Unknown GraphQL error')
                        logger.error(f"GraphQL error: {error_msg}")
                        if 'unauthorized' in error_msg.lower():
                            logger.error("Authentication failed - check your token")
                            return None
                    return data
                else:
                    logger.error(f"HTTP error {response.status}: {await response.text()}")
                    if response.status == 401:
                        logger.error("Authentication failed - check your token")
                        return None
                    elif response.status >= 500:
                        logger.error("Server error - will retry")
                    else:
                        logger.error("Client error - check your request")
                        return None
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
        except asyncio.TimeoutError:
            logger.error("Request timed out")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

        attempt += 1
        if attempt < max_attempts:
            wait_time = min(5 * 2 ** attempt, 30)
            logger.info(f"Retrying in {wait_time} seconds (attempt {attempt}/{max_attempts})...")
            await asyncio.sleep(wait_time)
        else:
            logger.error("Max retries reached")
    
    return None