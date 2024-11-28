from django.contrib import admin
from core.models.messagelog import MessageLogs
import logging

logger = logging.getLogger(__name__)

class TargetListAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact_type', 'contact_tag', 'contact_phone', 'sent_messages_count', 'sequence_order')
    list_filter = ('contact_type', 'contact_tag')
    search_fields = ('contact_phone', 'contact_tag')
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
        from django.core.management import call_command
        processed_tags = set()
        for target in queryset:
            if target.contact_tag not in processed_tags:
                try:
                    call_command('process_campaign', target.contact_tag)
                    self.message_user(
                        request,
                        f"Successfully processed target list with tag '{target.contact_tag}' to queue",
                        level='SUCCESS'
                    )
                    processed_tags.add(target.contact_tag)
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error processing target list with tag '{target.contact_tag}': {str(e)}",
                        level='ERROR'
                    )
    
    instant_process_tlist_to_queue.short_description = "🔄 Add to Queue"
