# messageShooter/services/messaging/text_sender.py

"""
Extract sending logic from send_message_async and send_file_message_async
Handle all communication with messaging APIs
Use the RateLimiter we just created
"""

import logging
import json
from typing import Dict, Any, Optional

from core.models.contact import Contact
from core.models.message import Message
from core.models.userphone import UserPhone

from messageShooter.services.messaging.rate_limiter import RateLimiter
from messageShooter.services.retry.retry_strategy import RetryStrategy
from apiSocialHub.resolvers.send_text_message import send_text_message

logger = logging.getLogger(__name__)

class TextSender:
    """
    Handles sending text-only messages through messaging APIs.
    Implements rate limiting and retry capabilities.
    """
    
    def __init__(self, rate_limiter: RateLimiter, retry_strategy: RetryStrategy):
        """
        Initialize the text sender with rate limiting and retry capabilities.
        
        Args:
            rate_limiter: Rate limiter for controlling send frequency
            retry_strategy: Retry strategy for handling failures
        """
        self.logger = logging.getLogger(__name__)
        self.rate_limiter = rate_limiter
        self.retry_strategy = retry_strategy
        self._test_mode = False
    
    async def send(self, contact: Contact, message: Message, userphone: UserPhone) -> bool:
        """
        Send a text-only message to a contact.
        
        Args:
            contact: The contact to send the message to
            message: The message content to send
            userphone: The userphone to use for sending
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        if self._test_mode:
            self.logger.info(f"TEST MODE: Would send text message to {contact.phone}: {message.text}")
            return True
        
        try:
            # Format the message for the specific contact
            formatted_message = self._format_message(message.text, contact)
            
            # Use retry strategy to handle potential failures
            result = await self.retry_strategy.execute(
                self._send_text,
                contact.phone,
                formatted_message,
                userphone.phone_token
            )
            
            return result.get('success', False)
            
        except Exception as e:
            self.logger.error(f"Error sending text message to {contact.phone}: {str(e)}", 
                             exc_info=True)
            return False
    
    async def _send_text(self, phone: str, message: str, token: str) -> Dict[str, Any]:
        """
        Execute the actual text sending operation.
        
        Args:
            phone: The phone number to send to
            message: The formatted message to send
            token: The authentication token for the messaging API
            
        Returns:
            Dict: Response from the messaging API
        """
        try:
            # The API expects positional parameters: phone, message, token_socialhub
            response = send_text_message(phone, message, token)
            
            # Parse the response JSON for better error handling
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except json.JSONDecodeError:
                    self.logger.warning(f"Could not parse response as JSON: {response}")
                    response = {'success': True, 'message': response}
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in _send_text: {str(e)}", exc_info=True)
            raise
    
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