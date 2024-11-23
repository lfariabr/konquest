from django.contrib import admin
from .models.campaign import Campaign
from .models.target_list import TargetList
from .models.queue import Queue
# from .models.job import Job

class TargetListAdmin(admin.ModelAdmin):
    list_display = ('contact_type', 'contact_tag', 'contact_phone', 'reference_id', 'sent_messages_count', 'userphone')
    search_fields = ('contact_type', 'contact_tag', 'contact_phone', 'reference_id')
    list_filter = ('contact_type', 'contact_tag', 'userphone')
    ordering = ('contact_type', 'contact_tag', 'contact_phone')
admin.site.register(TargetList, TargetListAdmin)

class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_type', 'contact_tag', 'frequency', 'start_time', 'campaign_status', 'userphone')
    search_fields = ('name', 'contact_type', 'contact_tag')
    list_filter = ('contact_type', 'contact_tag', 'campaign_status')
    ordering = ('contact_type', 'contact_tag', 'name')
admin.site.register(Campaign, CampaignAdmin)

admin.site.register(Queue)

# admin.site.register(Job)