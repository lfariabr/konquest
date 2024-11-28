from django.contrib import admin
from messageShooter.models.campaign import Campaign
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue
from .campaignAdmin import CampaignAdmin
from .targetListAdmin import TargetListAdmin
from .queueAdmin import QueueAdmin

# Register models with their respective admin classes
admin.site.register(Campaign, CampaignAdmin)
admin.site.register(TargetList, TargetListAdmin)
admin.site.register(Queue, QueueAdmin)
