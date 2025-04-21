"""
The retry logic from process_with_retry
Exponential backoff calculation from calculate_retry_delay
Different retry strategies (exponential, linear, etc.)
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Tuple, List, Optional, Any, Type, TypeVar, Union

# Type definition for callable to retry
T = TypeVar('T')
RetryCallable = Callable[[], T]

class RetryStrategyType(Enum):
    """Enum for retry strategies"""
    EXPONENTIAL = 'exponential'
    LINEAR = 'linear'
    FIXED = 'fixed'

class RetryStrategy:
    """
    A class for retrying operations with various strategies.
    
    This class supports:
    - Multiple retry strategies (exponential, linear, fixed)
    - Configurable retry attempts
    - Configurable retry delay
    - Configurable max delay
    - Test mode for bypassing delays
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: int = 20,
        max_delay: int = 300,
        strategy_type: RetryStrategyType = RetryStrategyType.EXPONENTIAL,
        retryable_errors: Optional[Tuple[Type[Exception], ...]] = None,
        test_mode: bool = False
    ):
        """
        Initialize the retry strategy.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds between retries
            max_delay: Maximum delay in seconds
            strategy_type: The retry strategy to use (exponential, linear, fixed)
            retryable_errors: Tuple of exception types that should trigger a retry
            test_mode: When True, bypasses delays for testing purposes
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy_type = strategy_type
        self._test_mode = test_mode

        # Default retryable errors
        self.retryable_errors = retryable_errors or (
            ConnectionError,
            ConnectionResetError,
            TimeoutError
        )

        self.logger = logging.getLogger(__name__)

    async def calculate_delay(self, attempt: int) -> int:
        """
        Calculate the delay before the next retry based on the strategy.
        
        Args:
            attempt: The current attempt number (0-based)
            
        Returns:
            int: The calculated delay in seconds
        """

        if self.strategy_type == RetryStrategyType.EXPONENTIAL:
            delay = min(self.max_delay, (2 ** attempt) * self.base_delay)
        elif self.strategy_type == RetryStrategyType.LINEAR:
            delay = min(self.max_delay, (attempt + 1) * self.base_delay)
        elif self.strategy_type == RetryStrategyType.FIXED:
            delay = self.base_delay
        else:
            delay = self.base_delay
            
        return delay
        
    def is_retryable_error(self, error: Exception) -> bool:
        """
        Check if an error should trigger a retry.
        
        Args:
            error: The exception to check
            
        Returns:
            bool: True if the error should trigger a retry, False otherwise
        """
        return isinstance(error, self.retryable_errors)
    
    async def execute(
        self, 
        func: RetryCallable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: The async function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Any: The result of the successful function call
            
        Raises:
            Exception: If all retry attempts fail, the last error is raised
        """
        attempt = 0
        last_error = None
        
        while attempt < self.max_retries:
            try:
                self.logger.info(f"Attempt {attempt + 1} of {self.max_retries}")
                result = await func(*args, **kwargs)
                
                # Handle tuple result format (success, error)
                if isinstance(result, tuple) and len(result) == 2:
                    success, error = result
                    if success:
                        return result
                    
                    # Check if error is retryable
                    if error and self.is_retryable_error(error):
                        last_error = error
                    else:
                        return result  # Don't retry non-retryable errors
                else:
                    return result  # Return non-tuple results directly
                
            except self.retryable_errors as e:
                last_error = e
                self.logger.warning(
                    f"Attempt {attempt + 1} failed with retryable error: {str(e)}. "
                    f"Retrying..."
                )
            
            except Exception as e:
                self.logger.error(f"Non-retryable error: {str(e)}")
                raise  # Don't retry non-retryable errors
            
            # Increment attempt and apply backoff
            attempt += 1
            if attempt < self.max_retries:
                delay = await self.calculate_delay(attempt - 1)
                if delay > 0:
                    self.logger.info(f"Waiting {delay} seconds before retry...")
                    await asyncio.sleep(delay)
        
        # All retries failed
        if isinstance(last_error, Exception):
            raise last_error
        return False, last_error
    
    def set_test_mode(self, enabled: bool) -> None:
        """
        Enable or disable test mode.
        In test mode, no delays are applied between retries.
        
        Args:
            enabled: Whether test mode should be enabled
        """
        self._test_mode = enabled
        self.logger.debug(f"Test mode {'enabled' if enabled else 'disabled'}")
    
    @property
    def test_mode(self) -> bool:
        """Get the current test mode status."""
        return self._test_mode

    def add_retryable_error(self, error_type: Type[Exception]) -> None:
        """
        Add a new exception type to the list of retryable errors.
        
        Args:
            error_type: The exception type to add
        """
        if not isinstance(self.retryable_errors, list):
            self.retryable_errors = list(self.retryable_errors)
        
        if error_type not in self.retryable_errors:
            self.retryable_errors.append(error_type)      
        
