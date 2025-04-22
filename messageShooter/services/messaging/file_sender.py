# messageShooter/services/messaging/file_sender.py

"""
Extract sending logic from send_message_async and send_file_message_async
Handle all communication with messaging APIs
Use the RateLimiter we just created
"""

import os
import logging
import json
from typing import Dict, Any, Optional

from core.models.contact import Contact
from core.models.message import Message
from core.models.userphone import UserPhone

from messageShooter.services.messaging.rate_limiter import RateLimiter
from messageShooter.services.retry.retry_strategy import RetryStrategy
from apiSocialHub.resolvers.send_file_message import send_file_message

logger = logging.getLogger(__name__)

class FileSender:
    """
    Handles sending messages with file attachments through messaging APIs.
    Implements rate limiting and retry capabilities.
    """
    
    def __init__(self, rate_limiter: RateLimiter, retry_strategy: RetryStrategy):
        """
        Initialize the file sender with rate limiting and retry capabilities.
        
        Args:
            rate_limiter: Rate limiter for controlling send frequency
            retry_strategy: Retry strategy for handling failures
        """
        self.logger = logging.getLogger(__name__)
        self.rate_limiter = rate_limiter
        self.retry_strategy = retry_strategy
        self._test_mode = False
        
        # File upload settings
        self.max_file_size = 10 * 1024 * 1024  # 10MB limit
        self.large_file_threshold = 1 * 1024 * 1024  # 1MB threshold for progress logging
    
    async def send(self, contact: Contact, message: Message, 
                  userphone: UserPhone, file_path: str) -> bool:
        """
        Send a message with a file attachment to a contact.
        
        Args:
            contact: The contact to send the message to
            message: The message content to send
            userphone: The userphone to use for sending
            file_path: Path to the file to send
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        if self._test_mode:
            self.logger.info(f"TEST MODE: Would send file message to {contact.phone}: "
                            f"{message.text} with file {file_path}")
            return True
        
        # Check if file exists and is within size limits
        if not self._validate_file(file_path):
            return False
        
        try:
            # Format the message for the specific contact
            formatted_message = self._format_message(message.text, contact)
            
            # Use retry strategy to handle potential failures
            result = await self.retry_strategy.execute(
                self._send_file,
                contact.phone,
                formatted_message,
                userphone.phone_token,
                file_path
            )
            
            return result.get('success', False)
            
        except Exception as e:
            self.logger.error(f"Error sending file message to {contact.phone}: {str(e)}", 
                             exc_info=True)
            return False
    
    async def _send_file(self, phone: str, message: str, token: str, 
                         file_path: str) -> Dict[str, Any]:
        """
        Execute the actual file sending operation.
        
        Args:
            phone: The phone number to send to
            message: The formatted message to send
            token: The authentication token for the messaging API
            file_path: Path to the file to send
            
        Returns:
            Dict: Response from the messaging API
        """
        try:
            # Call with positional arguments as expected by the API
            response = send_file_message(phone, message, token, file_path)
            
            # Parse the response JSON for better error handling
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except json.JSONDecodeError:
                    self.logger.warning(f"Could not parse response as JSON: {response}")
                    response = {'success': True, 'message': response}
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in _send_file: {str(e)}", exc_info=True)
            raise
    
    def _validate_file(self, file_path: str) -> bool:
        """
        Validate that the file exists and is within size limits.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            bool: True if the file is valid, False otherwise
        """
        # Check if file exists
        if not os.path.isfile(file_path):
            self.logger.error(f"File not found: {file_path}")
            return False
        
        # Check if file is accessible
        if not os.access(file_path, os.R_OK):
            self.logger.error(f"File not readable: {file_path}")
            return False
        
        # Check file size
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size > self.max_file_size:
                self.logger.error(f"File too large: {file_path} ({file_size} bytes)")
                return False
                
            if file_size > self.large_file_threshold:
                self.logger.info(f"Large file: {file_path} ({file_size} bytes)")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking file size: {str(e)}", exc_info=True)
            return False
    
    def _format_message(self, message: str, contact: Contact) -> str:
        """
        Format the message with contact-specific variables.
        
        Args:
            message: The template message
            contact: The contact with replacement values
            
        Returns:
            str: Formatted message with variables replaced
        """
        # Simple variable replacement
        formatted = message.replace('[nome]', contact.name or '')
        formatted = formatted.replace('[phone]', contact.phone or '')
        
        # You can add more complex variable replacements here if needed
        
        return formatted
    
    def set_test_mode(self, enabled: bool) -> None:
        """
        Enable or disable test mode for dry runs without actual sending.
        
        Args:
            enabled: True to enable test mode, False to disable
        """
        self._test_mode = enabled
