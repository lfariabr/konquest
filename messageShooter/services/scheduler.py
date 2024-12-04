from django.utils import timezone
from django.db import transaction
from messageShooter.models.campaign import Campaign
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue
from messageShooter.resolvers.target_list_resolver import generate_target_lists
import logging
from itertools import groupby
from operator import attrgetter

logger = logging.getLogger(__name__)

class CampaignScheduler:
    def process_campaigns(self):
        """Process all campaigns that are ready to run"""
        logger.info("Starting campaign processing")
        
        try:
            # Generate target lists for campaigns that are ready to run
            created_lists = generate_target_lists()
            
            if not created_lists:
                logger.info("No target lists were created")
                return 0

            # Move target lists to Queue
            queued_count = 0
            with transaction.atomic():
                # Group target lists by campaign
                sorted_targets = sorted(created_lists, key=attrgetter('campaign_id'))
                for campaign_id, campaign_targets in groupby(sorted_targets, key=attrgetter('campaign_id')):
                    campaign_targets = list(campaign_targets)  # Convert iterator to list
                    if not campaign_targets:
                        continue
                    
                    first_target = campaign_targets[0]
                    
                    # Check if queue already exists for this campaign
                    existing_queue = Queue.objects.filter(
                        campaign=first_target.campaign,
                        status__in=['pending', 'processing']
                    ).first()
                    
                    if existing_queue:
                        logger.info(f"Queue already exists for campaign {first_target.campaign.id}")
                        continue

                    contacts = first_target.get_contacts()
                    
                    # Create one queue for all target lists in this campaign
                    Queue.objects.create(
                        target_list=first_target,  # Use first target list as reference
                        campaign=first_target.campaign,
                        message=first_target.message,
                        userphone=first_target.userphone,
                        phone_token=first_target.token,
                        priority=first_target.priority if hasattr(first_target, 'priority') else 0,
                        scheduled_time=timezone.now(),
                        total_contacts=len(campaign_targets),  # Total contacts is number of target lists
                        processed_contacts={},
                        processed_count=0,
                        status='pending'
                    )
                    queued_count += 1
                    
                    # Update all target lists' status
                    for target in campaign_targets:
                        target.status = 'processing'
                        target.save()
                    
                    logger.info(f"Queued target list {first_target.id} for campaign {campaign_id}")
            
            logger.info(f"Successfully queued {queued_count} target lists")
            return queued_count
        
        except Exception as e:
            logger.error(f"Error processing campaign: {str(e)}")
            return 0