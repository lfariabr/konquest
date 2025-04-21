import asyncio
import time
import logging
from collections import defaultdict
from typing import Dict, Optional

class RateLimiter:
    """
    Handles rate limiting for message sending operations.
    Ensures that messages aren't sent too quickly to the same userphone.
    """

    def __init__(self, breath_time: int = 30, test_mode: bool = False):
        """
        Initialize the rate limiter
        
        Args:
            breath_time: Time in seconds to wait between messages for the same userphone
            test_mode: When True, bypasses rate limiting for testing purposes
        """
        self._userphone_locks: Dict[int, float] = {}
        self.breath_time = breath_time
        self._test_mode = test_mode
        self.logger = logging.getLogger(__name__)

    async def acquire_lock(self, userphone_id: int) -> float:
        """
        Acquire lock for a userphone with rate limiting.
        If the userphone has sent a message recently, this method will
        wait until enough time has passed before returning.
        
        Args:
            userphone_id: ID of the userphone to acquire lock for
            
        Returns:
            float: Current timestamp when lock was acquired
        """
        current_time = time.time()
        last_send_time = self._userphone_locks.get(userphone_id, 0)

        # Check if we need to wait based on rate limits
        if not self._test_mode and current_time - last_send_time < self.breath_time:
            wait_time = self.breath_time - (current_time - last_send_time)
            self.logger.debug(f"Rate limit reached for userphone {userphone_id}. Waiting {wait_time:.2f} seconds.")
            await asyncio.sleep(wait_time)
        
        # Update the last send time for userphone
        self._userphone_locks[userphone_id] = time.time()
        return current_time


    def release_lock(self, userphone_id: int) -> None:
        """
        Release lock for a userphone.
        This does not actually release the lock, as it's time-based,
        but can be used for cleanup or to implement future cancellation logic.
        
        Args:
            userphone_id: ID of the userphone to release lock for
        """
        # In the current implementation, we don't need to do anything
        # The time-based approach automatically handles lock expiry
        pass

    def set_breath_time(self, seconds: int) -> None:
        """
        Update the breath time between messages
        
        Args:
            seconds: New breath time in seconds
        """
        self.breath_time = seconds
        self.logger.debug(f"Breath time updated to {self.breath_time} seconds.")
    
    def set_test_mode(self, enabled: bool) -> None:
        """
        Enable or disable test mode
        
        Args:
            enabled: When True, bypasses rate limiting for testing purposes
        """
        self._test_mode = enabled
        self.logger.debug(f"Test mode {'enabled' if enabled else 'disabled'}.")

    def clear_locks(self) -> None:
        """
        Clear all locks, effectively resetting the rate limiter.
        This is useful for testing or when you want to reset the state.
        """
        self._userphone_locks.clear()
        self.logger.debug("All locks cleared.")