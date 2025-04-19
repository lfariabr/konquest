import asyncio
from collections import defaultdict

class RateLimiter:
    async def acquire_lock(self, userphone_id: int) -> float:
        """Acquire lock for a userphone with rate limiting"""
        pass

    def release_lock(self, userphone_id: int) -> None:
        """Release lock for a userphone"""
        pass