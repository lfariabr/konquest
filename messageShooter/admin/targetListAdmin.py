from django.contrib import admin
from core.models.messagelog import MessageLogs
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class TargetListAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'contact_type',
        'contact_tag',
        'campaign',
        'contact_phone',
        'sent_messages_count',
        'status',
        'created_at',
        'updated_at'
    )
    list_filter = ('contact_type', 'contact_tag', 'campaign', 'status', 'created_at')
    search_fields = ('contact_phone', 'contact_tag', 'campaign__name')
    readonly_fields = ('sent_messages_count',)
    actions = ['instant_process_tlist_to_queue']

    def sent_messages_count(self, obj):
        """Return count of sent messages for this target's contact and tag"""
        # Debug info
        logger.info(f"\n=== Counting messages for target list entry ===")
        logger.info(f"Target List: {obj.id}")
        logger.info(f"Phone: {obj.contact_phone}")
        logger.info(f"Tag: {obj.contact_tag}")
        
        if not obj.contact:
            logger.info("No contact associated with target list entry")
            return 0
            
        logger.info(f"Contact: id={obj.contact.id}, phone={obj.contact.phone}, tag={obj.contact.relationship_tag}")
        
        # Get all messages for this contact that are sent
        logs = MessageLogs.objects.filter(
            contact=obj.contact,
            status='sent'
        )
        
        count = logs.count()
        logger.info(f"Found {count} sent messages for contact {obj.contact.id}")
        for log in logs:
            logger.info(f"Message: id={log.id}, status={log.status}, tag={log.relationship_tag}, sent_at={log.sent_at}")
        logger.info("=== End message count ===\n")
        
        return count
    sent_messages_count.short_description = '📨 Sent Messages'

    def instant_process_tlist_to_queue(self, request, queryset):
        """Directly add selected target lists to the queue"""
        from messageShooter.models.queue import Queue
        
        success_count = 0
        error_count = 0
        
        for target in queryset:
            try:
                # Get contacts for this target list
                contacts = target.get_contacts()
                if not contacts:
                    self.message_user(
                        request,
                        f"No contacts found for target list {target.id}",
                        level='WARNING'
                    )
                    continue
                    
                # Get current counter for contact
                from messageShooter.resolvers.get_counter import get_counter_whatsapp
                counter = get_counter_whatsapp(target.contact_phone, target.contact_tag)
                
                # Get message for current counter
                from core.models.message import Message
                message = Message.objects.filter(
                    relationship_tag=target.contact_tag,
                    contact_type=target.contact_type,
                    counter=counter
                ).first()
                
                if not message:
                    self.message_user(
                        request,
                        f"No message found for counter {counter} and tag {target.contact_tag}",
                        level='WARNING'
                    )
                    continue
                
                # Create queue entry
                Queue.objects.create(
                    target_list=target,
                    message=message,  # Use message for current counter
                    userphone=target.userphone,
                    phone_token=target.userphone.phone_token,
                    status='pending',
                    scheduled_time=timezone.now(),
                    total_contacts=len(contacts),
                    processed_contacts={},
                    processed_count=0
                )
                success_count += 1
                
                # Update target list status
                target.status = 'processing'
                target.save()
                
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error adding target list {target.id} to queue: {str(e)}",
                    level='ERROR'
                )
        
        if success_count > 0:
            self.message_user(
                request,
                f"Successfully added {success_count} target list(s) to queue",
                level='SUCCESS'
            )
        
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to add {error_count} target list(s) to queue",
                level='WARNING'
            )

    instant_process_tlist_to_queue.short_description = "🔄 Add to Queue"
