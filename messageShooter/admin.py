from django.contrib import admin
from django.utils import timezone
from .models.campaign import Campaign
from .models.target_list import TargetList
from .models.queue import Queue
# from .models.job import Job
from messageShooter.resolvers.target_list_resolver import create_target_list
from django.db import models

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_type', 'contact_tag', 'frequency', 'start_time', 'campaign_status', 'userphone', 'next_run']
    search_fields = ('name', 'contact_type', 'contact_tag')
    list_filter = ('contact_type', 'contact_tag', 'campaign_status')
    ordering = ('contact_type', 'contact_tag', 'name')
    actions = ['instant_generate_tlist']
    
    def instant_generate_tlist(self, request, queryset):
        total_created = 0
        for campaign in queryset:
            try:
                # Create target list with force_run=True to bypass checks
                created, skipped, errors = create_target_list(campaign.id, force_run=True)
                total_created += created
                
                if created > 0:
                    self.message_user(
                        request,
                        f"YEAH! Target List created!\nFound {created} contacts for campaign {campaign.name}",
                        level="success"
                    )
                else:
                    self.message_user(
                        request,
                        f"No contacts found for campaign {campaign.name}",
                        level="warning"
                    )
            except Exception as e:
                self.message_user(
                    request,
                    f"Error creating target list for campaign {campaign.name}: {str(e)}",
                    level="error"
                )
    
    instant_generate_tlist.short_description = "🎯 Create Target List"

class TargetListAdmin(admin.ModelAdmin):
    list_display = ('contact_type', 'contact_tag', 'contact_phone', 'reference_id', 'sent_messages_count', 'userphone') 
    search_fields = ('contact_type', 'contact_tag', 'contact_phone', 'reference_id')
    list_filter = ('contact_type', 'contact_tag', 'userphone')
    ordering = ('contact_type', 'contact_tag', 'contact_phone')
    actions = ['instant_process_tlist_to_queue']

    def sent_messages_count(self, obj):
        """Return count of sent messages for this target's contact and tag"""
        from core.models.messagelog import MessageLogs
        import logging
        logger = logging.getLogger(__name__)
        
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
                        f"Successfully processed target list with tag '{target.contact_tag}' to queue"
                    )
                    processed_tags.add(target.contact_tag)
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error processing target list with tag '{target.contact_tag}': {str(e)}",
                        level='ERROR'
                    )
    
    instant_process_tlist_to_queue.short_description = "🔄 Add to Queue"

admin.site.register(TargetList, TargetListAdmin)

class QueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact_type', 'status', 'recipients_count', 'userphone_number', 'target_list_link')
    list_filter = ('status', 'target_list__contact_type', 'userphone')
    search_fields = ('target_list__contact_tag', 'contact__phone', 'userphone__phone_number')
    ordering = ('-priority', 'scheduled_time', 'created_at')
    actions = ['instant_process_queue']

    def contact_type(self, obj):
        return obj.target_list.contact_type if obj.target_list else '-'
    contact_type.short_description = 'Contact Type'
    
    def recipients_count(self, obj):
        """Return count of recipients in the target list"""
        if not obj.target_list:
            return 0
        return TargetList.objects.filter(contact_tag=obj.target_list.contact_tag).count()
    recipients_count.short_description = 'Recipients'

    def userphone_number(self, obj):
        return obj.userphone.phone_number if obj.userphone else '-'
    userphone_number.short_description = 'UserPhone Number'

    def target_list_link(self, obj):
        if not obj.target_list:
            return '-'
        from django.utils.html import format_html
        url = f"/admin/messageShooter/targetlist/{obj.target_list.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.target_list.id)
    target_list_link.short_description = 'Target List'

    def instant_process_queue(self, request, queryset):
        from django.core.management import call_command
        processed = 0
        errors = []
        
        for queue_entry in queryset:
            try:
                # Call the process_queue command for each selected queue entry
                call_command('process_queue', queue_id=queue_entry.id)
                processed += 1
                self.message_user(
                    request,
                    f"Successfully processed queue entry {queue_entry.id}",
                    level='SUCCESS'
                )
            except Exception as e:
                errors.append(f"Queue {queue_entry.id}: {str(e)}")
                self.message_user(
                    request,
                    f"Error processing queue entry {queue_entry.id}: {str(e)}",
                    level='ERROR'
                )
        
        if processed > 0:
            self.message_user(
                request,
                f"Successfully processed {processed} queue entries",
                level='SUCCESS'
            )
        
        if errors:
            self.message_user(
                request,
                "Errors encountered:\n" + "\n".join(errors),
                level='ERROR'
            )
    
    instant_process_queue.short_description = "💥 Process Queue"

admin.site.register(Queue, QueueAdmin)

# admin.site.register(Job)