from django.utils import timezone
from django.db import transaction
from messageShooter.models.queue import Queue
from apiSocialHub.resolvers.send_text_message import send_text_message
from apiSocialHub.resolvers.send_file_message import send_file_message
from core.models.messagelog import MessageLogs
import logging
from django.db.models import Q

logger = logging.getLogger(__name__)

class QueueProcessor:
    max_retries = 3
    base_retry_delay = 5  # Base delay in minutes

    def process_queue(self, batch_size=50):
        """Process pending queue items"""
        logger.info("Starting queue processing")
        
        try:
            now = timezone.now()
            # Get pending messages that are scheduled for now or earlier
            pending_items = Queue.objects.filter(
                Q(status='pending') | Q(status='retrying'),
                scheduled_time__lte=now
            ).select_related('target_list', 'message', 'userphone')[:batch_size]
            
            processed_count = 0
            success_count = 0
            error_count = 0
            
            for queue_item in pending_items:
                success, error = self.process_queue_item(queue_item)
                processed_count += 1
                if success:
                    success_count += 1
                if error:
                    error_count += 1
            
            logger.info(f"Queue processing complete: {processed_count} processed, {success_count} successful, {error_count} errors")
            return processed_count, success_count, error_count
            
        except Exception as e:
            logger.error(f"Error in queue processing: {str(e)}")
            return 0, 0, 0

    def process_queue_item(self, queue_item):
        """Process a single queue item (target list)"""
        if queue_item.status not in ['pending', 'retrying']:
            return False, False
        
        success_count = 0
        error_count = 0
        
        try:
            # Mark as processing
            queue_item.status = 'processing'
            queue_item.save()
            
            # Get target list contacts
            contact = queue_item.target_list.contact
            
            if contact:
                try:
                    # Send message to contact
                    success, error_message = self.send_message(
                        contact=contact,
                        message=queue_item.message,
                        userphone=queue_item.userphone
                    )
                    
                    if success:
                        success_count += 1
                        queue_item.status = 'sent'
                        queue_item.sent_at = timezone.now()
                    else:
                        error_count += 1
                        # If we haven't exceeded max retries, mark for retry
                        if queue_item.retry_count < self.max_retries:
                            queue_item.status = 'retrying'
                            queue_item.retry_count += 1
                            # Calculate next retry time with exponential backoff
                            retry_delay = self.base_retry_delay * (2 ** (queue_item.retry_count - 1))
                            queue_item.scheduled_time = timezone.now() + timezone.timedelta(minutes=retry_delay)
                        else:
                            queue_item.status = 'failed'
                            queue_item.last_error = error_message if error_message else "Max retries exceeded"
                    
                except Exception as e:
                    error_count += 1
                    queue_item.status = 'failed'
                    queue_item.last_error = str(e)
            
            queue_item.save()
            success = success_count > 0
            error = error_count > 0
            logger.info(f"{'Successfully' if success else 'Failed to'} process queue entry {queue_item.id} (Status: {queue_item.status})")
            return success, error
            
        except Exception as e:
            queue_item.status = 'failed'
            queue_item.last_error = str(e)
            queue_item.save()
            logger.error(f"Failed to process queue entry {queue_item.id} due to error: {str(e)}")
            return False, True

    def send_message(self, contact, message, userphone):
        """Send a message to a contact"""
        try:
            # Check if this is a file message
            message_type = getattr(message, 'file_type', None)
            success = False
            error_message = None
            
            if message_type:  
                success, error_message = send_file_message(
                    phone=contact.phone,
                    message=message.text,
                    token_socialhub=userphone.phone_token,
                    file_path=message.file.path if message.file else None  
                )
            else:
                success = send_text_message(
                    phone=contact.phone,
                    message=message.text,
                    token_socialhub=userphone.phone_token
                )
            
            # Create message log with status
            status = 'sent' if success else f'failed: {error_message}' if error_message else 'failed'
            MessageLogs.objects.create(
                user=contact.user,
                contact=contact,
                message=message,
                status=status,
                user_phone=userphone,
                relationship_tag=message.relationship_tag  
            )
            
            # Return both success and error message for queue entry
            return success, error_message
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error sending message: {error_str}")
            # Create error log
            MessageLogs.objects.create(
                user=contact.user,
                contact=contact,
                message=message,
                status=f'failed: {error_str}',
                user_phone=userphone,
                relationship_tag=message.relationship_tag  
            )
            return False, error_str