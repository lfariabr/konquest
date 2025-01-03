from django.contrib import admin
from django.utils.html import format_html
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue
from messageShooter.services.queue_processor import QueueProcessor
from django.core.cache import cache
import logging
from django.db.models import Prefetch
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

class QueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_contact_type', 'get_campaign_name', 'status', 'get_recipients_count', 'get_userphone_number', 'get_target_list_link')
    list_filter = ('status', 'target_list__contact_type', 'target_list__campaign', 'userphone')
    search_fields = ('target_list__contact_tag', 'contact__phone', 'userphone__phone_number', 'target_list__campaign__name')
    ordering = ('-priority', 'scheduled_time', 'created_at')
    actions = ['instant_process_queue', 'resume_interrupted_queues']

    def get_queryset(self, request):
        """Override get_queryset to optimize queries and batch load data"""
        self.request = request
        queryset = super().get_queryset(request)
        
        # Prefetch all target lists at once with all needed relations
        return queryset.select_related(
            'target_list',
            'target_list__campaign',
            'target_list__userphone',
            'target_list__contact',
            'userphone'
        )

    def get_contact_type(self, obj):
        return obj.target_list.contact_type if obj.target_list else '-'
    get_contact_type.short_description = 'Contact Type'
    
    def get_progress_display(self, obj):
        """Show processing progress for queue with caching"""
        cache_key = f'queue_progress_{obj.id}'
        
        if not hasattr(self, 'request'):
            logger.error("No request object found for progress display")
            return '-'
            
        # Try to get from cache
        if cache_key in self.request.queue_counters:
            logger.debug(f"Cache hit for progress {cache_key}")
            return self.request.queue_counters[cache_key]
            
        if not obj.processed_contacts:
            self.request.queue_counters[cache_key] = '-'
            return '-'
        
        try:
            total = self.get_recipients_count(obj)
            processed = len(obj.processed_contacts)
            success = len([c for c in obj.processed_contacts.values() if c["status"] == "sent"])
            
            result = None
            if obj.status == 'processing':
                result = format_html(
                    '<span style="color: #1a73e8;">⏳ {}/{} ({:.0f}%)</span>',
                    processed, total, (processed/total*100) if total > 0 else 0
                )
            elif obj.status == 'sent':
                result = format_html(
                    '<span style="color: #0d904f;">✓ {}/{}</span>',
                    success, total
                )
            elif obj.status == 'failed':
                result = format_html(
                    '<span style="color: #d93025;">✗ {}/{}</span>',
                    success, total
                )
            elif obj.status == 'retrying':
                result = format_html(
                    '<span style="color: #f29900;">↻ {}/{} (Retry #{}/3)</span>',
                    success, total, obj.retry_count
                )
            else:
                result = format_html(
                    '{}/{}',
                    success, total
                )
                
            # Cache the result
            self.request.queue_counters[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error displaying progress for queue {obj.id}: {str(e)}")
            self.request.queue_counters[cache_key] = '-'
            return '-'
    get_progress_display.short_description = '📊 Progress'
    
    def get_recipients_count(self, obj):
        """Get count of recipients for this queue item with caching"""
        if not obj.target_list:
            return '-'
            
        cache_key = f'queue_recipients_count_{obj.id}'
        count = cache.get(cache_key)
        
        if count is not None:
            return count
            
        # Get count from target list with caching
        try:
            contacts = obj.target_list.get_contacts()
            count = len(contacts) if contacts else 0
            
            # Cache for 5 minutes for appointments, 1 hour for others
            timeout = 300 if obj.target_list.contact_type == 'Appointment' else 3600
            cache.set(cache_key, count, timeout=timeout)
            
            return count
        except Exception as e:
            logger.error(f"Error getting recipients count for queue {obj.id}: {str(e)}")
            return 0
    get_recipients_count.short_description = '👥 Recipients'

    def get_userphone_number(self, obj):
        return obj.userphone.phone_number if obj.userphone else '-'
    get_userphone_number.short_description = '📱 UserPhone'

    def get_target_list_link(self, obj):
        if not obj.target_list:
            return '-'
        url = f"/admin/messageShooter/targetlist/{obj.target_list.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.target_list.id)
    get_target_list_link.short_description = '🎯 Target List'

    def get_campaign_name(self, obj):
        if obj.target_list and obj.target_list.campaign:
            url = f"/admin/messageShooter/campaign/{obj.target_list.campaign.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.target_list.campaign.name)
        return '-'
    get_campaign_name.short_description = '📢 Campaign'

    def get_contact_count(self, obj):
        """Get count of contacts for this queue item"""
        if obj.target_list:
            contacts = obj.target_list.get_contacts()
            return len(contacts) if contacts else 0
        return 0
    get_contact_count.short_description = 'Contact Count'

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
    
    def changelist_view(self, request, extra_context=None):
        """Override changelist view to add performance monitoring"""
        from django.db import connection
        from time import time
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Start timing
        start_time = time()
        initial_queries = len(connection.queries)
        
        try:
            response = super().changelist_view(request, extra_context)
            
            # Log performance metrics
            end_time = time()
            total_queries = len(connection.queries) - initial_queries
            execution_time = end_time - start_time
            
            logger.info(
                f"Queue list view performance: {total_queries} queries in {execution_time:.2f}s"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in queue list view: {str(e)}")
            raise
    
    def save_model(self, request, obj, form, change):
        """Override save to handle contact count"""
        super().save_model(request, obj, form, change)
        
        # Invalidate cache after save
        if obj.target_list:
            obj.target_list.invalidate_contacts_cache()
    
    instant_process_queue.short_description = "💥 Process Queue"
    resume_interrupted_queues.short_description = "▶️ Resume interrupted Queue"
