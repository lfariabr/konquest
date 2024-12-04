from django.contrib import admin
from django.utils.html import format_html
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue
from messageShooter.services.queue_processor import QueueProcessor
import logging
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

class QueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact_type', 'campaign_name', 'status', 'progress_display', 'recipients_count', 'userphone_number', 'target_list_link')
    list_filter = ('status', 'target_list__contact_type', 'target_list__campaign', 'userphone')
    search_fields = ('target_list__contact_tag', 'contact__phone', 'userphone__phone_number', 'target_list__campaign__name')
    ordering = ('-priority', 'scheduled_time', 'created_at')
    actions = ['instant_process_queue', 'resume_interrupted_queues']

    def contact_type(self, obj):
        return obj.target_list.contact_type if obj.target_list else '-'
    contact_type.short_description = 'Contact Type'
    
    def progress_display(self, obj):
        """Show processing progress for queue"""
        if not obj.processed_contacts:
            return '-'
        
        try:
            total = len(obj.target_list.get_contacts()) if obj.target_list else 0
            processed = len(obj.processed_contacts)
            success = len([c for c in obj.processed_contacts.values() if c["status"] == "sent"])
            
            if obj.status == 'processing':
                return format_html(
                    '<span style="color: #1a73e8;">⏳ {}/{} ({:.0f}%)</span>',
                    processed, total, (processed/total*100) if total > 0 else 0
                )
            elif obj.status == 'sent':
                return format_html(
                    '<span style="color: #0d904f;">✓ {}/{}</span>',
                    success, total
                )
            elif obj.status == 'failed':
                return format_html(
                    '<span style="color: #d93025;">✗ {}/{}</span>',
                    success, total
                )
            elif obj.status == 'retrying':
                return format_html(
                    '<span style="color: #f29900;">↻ {}/{} (Retry #{}/3)</span>',
                    success, total, obj.retry_count
                )
            return f"{success}/{total}"
        except Exception as e:
            logger.error(f"Error displaying progress for queue {obj.id}: {str(e)}")
            return '-'
    progress_display.short_description = '📊 Progress'
    
    def recipients_count(self, obj):
        """Get total number of recipients in target list"""
        if not obj.target_list:
            return 0
        try:
            return len(obj.target_list.get_contacts())
        except Exception as e:
            logger.error(f"Error getting recipients count for queue {obj.id}: {str(e)}")
            return 0
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
        """Process selected queues immediately"""
        from messageShooter.resolvers.get_userphone import get_userphone
        
        logger.info("🚀 Admin: Starting to process %d queues...", len(queryset))
        processor = QueueProcessor()
        
        # Prepare queues with their userphones
        ready_queues = []
        for queue in queryset:
            try:
                # Get userphone for this queue's tag
                userphone, phone_token = get_userphone(queue.target_list.contact_tag)
                if not userphone:
                    self.message_user(
                        request,
                        f"No userphone found for tag {queue.target_list.contact_tag}",
                        level='WARNING'
                    )
                    continue
                
                # Update queue with resolved userphone and set status to processing
                queue.userphone = userphone
                queue.phone_token = phone_token
                queue.status = 'processing'  # Set status to processing before starting
                queue.save()
                ready_queues.append(queue)
                
            except Exception as e:
                logger.error(f"❌ Error preparing queue {queue.id}: {str(e)}")
                self.message_user(
                    request,
                    f"Error preparing queue {queue.id}: {str(e)}",
                    level='ERROR'
                )
        
        if ready_queues:
            try:
                # Process all queues concurrently
                success_count, error_count, exception_count = async_to_sync(processor.process_queues_async)(
                    pending_queues=ready_queues,
                    max_concurrent=len(ready_queues)  # Allow all queues to run concurrently
                )
                
                # Log results
                logger.info(
                    f"📊 Queue processing results:\n"
                    f"   - Total Queues: {len(ready_queues)}\n"
                    f"   - Successful: {success_count}\n"
                    f"   - Failed: {error_count}\n"
                    f"   - Exceptions: {exception_count}"
                )
                
                # Update queryset to refresh from database
                processed_queues = Queue.objects.filter(id__in=[q.id for q in ready_queues])
                failed_queues = processed_queues.filter(status__in=['failed', 'partially_completed'])
                
                # Prepare status message
                if failed_queues:
                    failed_ids = ", ".join(str(q.id) for q in failed_queues)
                    msg = (f"Processed {len(ready_queues)} queues: {success_count} successful, "
                          f"{error_count} failed, {exception_count} exceptions. "
                          f"Failed queues: {failed_ids}")
                    level = 'WARNING'
                else:
                    msg = f"Successfully processed {success_count} queues"
                    level = 'SUCCESS'
                
                self.message_user(request, msg, level=level)
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Error processing queues: {error_msg}", exc_info=True)
                self.message_user(
                    request,
                    f"Error processing queues: {error_msg}",
                    level='ERROR'
                )
    
    def resume_interrupted_queues(self, request, queryset):
        """Resume interrupted queues"""
        processor = QueueProcessor()
        
        try:
            total_queues = len(queryset)
            logger.info(f"🔄 Admin: Starting to resume {total_queues} interrupted queues...")
            
            # Run async function in sync context
            success_count, error_count, exception_count = async_to_sync(processor.process_queues_async)(
                max_concurrent=3,
                batch_size=total_queues
            )
            
            # Log detailed results
            logger.info(
                f"📊 Admin: Queue resume results:\n"
                f"   - Total Queues: {total_queues}\n"
                f"   - Successful: {success_count}\n"
                f"   - Failed: {error_count}\n"
                f"   - Exceptions: {exception_count}"
            )
            
            self.message_user(
                request,
                f"Resumed {total_queues} queues: {success_count} successful, {error_count} failed, {exception_count} exceptions",
                level='SUCCESS' if error_count == 0 and exception_count == 0 else 'WARNING'
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Admin: Error resuming queues: {error_msg}", exc_info=True)
            self.message_user(
                request,
                f"Error resuming queues: {error_msg}",
                level='ERROR'
            )
    
    instant_process_queue.short_description = "💥 Process Queue"
    resume_interrupted_queues.short_description = "▶️ Resume interrupted Queue"
