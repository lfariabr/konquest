# messageShooter/services/contact_processor.py

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from django.utils import timezone

from core.models.contact import Contact
from messageShooter.models.queue import Queue
from messageShooter.models.target_list import TargetList
from messageShooter.services.messaging.text_sender import TextSender
from messageShooter.services.messaging.file_sender import FileSender

class ContactProcessor:
    """Handles processing of contacts in batches for message sending."""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self._locks = {}

    async def process_contact_batch(
        self,
        contacts: List[Contact],
        queue: Queue,
        target_list: TargetList,
        userphone_getter,
        batch_size: int = 10,
    ) -> Tuple[Dict[str, Any]]:
        """
        Process a batch of contacts, sending messages to each.
        
        Args:
            contacts: List of contacts to process
            queue: The queue item being processed
            target_list: The target list containing configuration
            userphone_getter: Function to get userphone for sending
            batch_size: Number of contacts to process concurrently
            
        Returns:
            Dictionary mapping contact IDs to processing results
        """
        processed_results = {}
        for i in range(0, len(contacts), batch_size):
            batch = contacts[i:i + batch_size]
            tasks = [
                self._process_single_contact(
                    contact, queue, target_list, userphone_getter
                )
                for contact in batch
            ]
            batch_results = await asyncio.gather(*tasks)

            # Merge results
            for contact, result in zip(batch, batch_results):
                processed_results[contact.id] = result
        return processed_results

    async def _process_single_contact(
        self,
        contact: Contact,
        queue: Queue,
        target_list: TargetList,
        userphone_getter,
    ) -> Dict[str, Any]:
        """Process a single contact, returning the result."""
        result = {
            "status": "pending",
            "processed_at": timezone.now().isoformat(),
        }

        try:
            # Get userphone for sending
            userphone = await userphone_getter(contact)
            if not userphone:
                result["status"] = "skipped"
                result["error"] = "Userphone not found"
                return result
            
            await self._apply_rate_limiting(contact.phone)
            
            if queue.file:
                await self._send_file_message(contact, queue, userphone)
                result["status"] = "success"
                result["type"] = "file"
            else:
                await self._send_text_message(contact, queue, userphone)
                result["status"] = "success"
                result["type"] = "text"

        except Exception as e:
            self.logger.error(f"Error processing contact {contact.id}: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)
        finally:
            # Release rate limiting lock if it exists
            self._release_rate_limiting(contact.phone)
            
        return result
    
    async def _apply_rate_limiting(self, phone: str) -> None:
        """Apply rate limiting for a specific phone number."""
        phone_key = f"phone_lock_{phone}"
        if phone_key in self._locks:
            self.logger.info(f"⏳ Waiting for rate limit on phone {phone}...")
            await self._locks[phone_key].acquire()
        else:
            self._locks[phone_key] = asyncio.Lock()
            await self._locks[phone_key].acquire()
    
    def _release_rate_limiting(self, phone: str) -> None:
        """Release rate limiting lock for a phone number."""
        phone_key = f"phone_lock_{phone}"
        if phone_key in self._locks and self._locks[phone_key].locked():
            self._locks[phone_key].release()
    
    async def _send_text_message(self, contact, queue, userphone) -> None:
        """Send a text message to a contact."""
        # Create text sender
        text_sender = TextSender(
            user_token=userphone.token,
            debug=queue.debug,
            logger=self.logger
        )
        
        # Format and send message
        formatted_message = self._format_message(queue.message, contact)
        await text_sender.send(
            phone=contact.phone,
            message=formatted_message,
            preview_url=queue.preview_url
        )
    
    async def _send_file_message(self, contact, queue, userphone) -> None:
        """Send a file message to a contact."""
        # Create file sender
        file_sender = FileSender(
            user_token=userphone.token,
            debug=queue.debug,
            logger=self.logger
        )
        
        # Format and send message
        formatted_message = self._format_message(queue.message, contact)
        await file_sender.send(
            phone=contact.phone,
            message=formatted_message,
            file_path=queue.file.path,
            preview_url=queue.preview_url
        )
    
    def _format_message(self, message_template: str, contact: Contact) -> str:
        """Format message template with contact information."""
        # Basic implementation - can be expanded
        formatted = message_template
        
        # Replace contact fields
        for field in ['name', 'phone', 'email', 'store']:
            if hasattr(contact, field) and getattr(contact, field):
                formatted = formatted.replace(f"{{{field}}}", str(getattr(contact, field)))
        
        return formatted