from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from core.models.messagelog import MessageLogs
from messageShooter.models.target_list import TargetList
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=TargetList)
def initialize_target_list_counter(sender, instance, **kwargs):
    """
    Initialize sent_messages_count for new target lists based on existing message history
    """
    if instance._state.adding:  # Only for new instances
        try:
            # Get total sent messages for this contact and tag
            sent_count = MessageLogs.objects.filter(
                contact=instance.contact,
                relationship_tag=instance.contact_tag,
                status="sent"
            ).count()
            
            # Set initial count
            instance.sent_messages_count = sent_count
            logger.info(f"Initialized sent_messages_count to {sent_count} for new target list")
                
        except Exception as e:
            logger.error(f"Error initializing target list counter: {str(e)}")

@receiver(post_save, sender=MessageLogs)
def update_target_list_counter(sender, instance, created, **kwargs):
    """
    Update the sent_messages_count in TargetList when a message is sent
    """
    if created and instance.status == "sent":
        try:
            # Get total sent messages for this contact and tag
            sent_count = MessageLogs.objects.filter(
                contact=instance.contact,
                relationship_tag=instance.relationship_tag,
                status="sent"
            ).count()
            
            # Update all target lists for this contact and tag
            # Note: Using a transaction to ensure atomic update
            from django.db import transaction
            with transaction.atomic():
                target_lists = TargetList.objects.filter(
                    contact=instance.contact,
                    contact_tag=instance.relationship_tag
                ).select_for_update()
                
                updated = target_lists.update(sent_messages_count=sent_count)
                
                if updated:
                    logger.info(f"Updated sent_messages_count for {updated} target list(s) to {sent_count}")
                else:
                    logger.warning(f"No target lists found for contact {instance.contact.id} and tag {instance.relationship_tag}")
                
        except Exception as e:
            logger.error(f"Error updating target list counter: {str(e)}")
