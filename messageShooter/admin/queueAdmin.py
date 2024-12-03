from django.contrib import admin
from django.utils.html import format_html
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue
from messageShooter.services.queue_processor import QueueProcessor

class QueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact_type', 'campaign_name', 'status', 'recipients_count', 'userphone_number', 'target_list_link')
    list_filter = ('status', 'target_list__contact_type', 'target_list__campaign', 'userphone')
    search_fields = ('target_list__contact_tag', 'contact__phone', 'userphone__phone_number', 'target_list__campaign__name')
    ordering = ('-priority', 'scheduled_time', 'created_at')
    actions = ['instant_process_queue', 'resume_interrupted_queues']

    def contact_type(self, obj):
        return obj.target_list.contact_type if obj.target_list else '-'
    contact_type.short_description = 'Contact Type'
    
    def recipients_count(self, obj):
        """Return count of recipients in the target list"""
        if not obj.target_list:
            return 0
        return TargetList.objects.filter(contact_tag=obj.target_list.contact_tag).count()
    recipients_count.short_description = '👥 Recipients'

    def userphone_number(self, obj):
        return obj.userphone.phone_number if obj.userphone else '-'
    userphone_number.short_description = '📱 UserPhone'

    def target_list_link(self, obj):
        if not obj.target_list:
            return '-'
        url = f"/admin/messageShooter/targetlist/{obj.target_list.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.target_list.id)
    target_list_link.short_description = '🎯 Target List'

    def campaign_name(self, obj):
        if obj.target_list and obj.target_list.campaign:
            url = f"/admin/messageShooter/campaign/{obj.target_list.campaign.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.target_list.campaign.name)
        return '-'
    campaign_name.short_description = '📢 Campaign'

    def instant_process_queue(self, request, queryset):
        """Process selected queue entries immediately"""
        from messageShooter.services.queue_processor import QueueProcessor
        processor = QueueProcessor()
        processed = 0
        errors = []
        
        for queue_entry in queryset:
            try:
                success, error = processor.process_queue_item(queue_entry)
                processed += 1
                # Refresh to get latest status
                queue_entry.refresh_from_db()
                status_message = (
                    f"Queue entry {queue_entry.id} processed (Status: {queue_entry.status})"
                    + (f", Error: {queue_entry.last_error}" if queue_entry.last_error else "")
                )
                self.message_user(
                    request,
                    status_message,
                    level='SUCCESS' if queue_entry.status == 'sent' else 'WARNING'
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

    def resume_interrupted_queues(self, request, queryset):
        processor = QueueProcessor()
        resumed = 0
        
        for queue in queryset:
            if queue.status == 'interrupted':
                success, _ = processor.resume_interrupted_queue(queue)
                if success:
                    resumed += 1
        
        self.message_user(
            request,
            f"Successfully resumed {resumed} queue(s)."
        )
    
    resume_interrupted_queues.short_description = "▶️ Resume interrupted Queue"
