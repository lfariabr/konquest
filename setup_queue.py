import os
import django
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konquist.settings')
django.setup()

from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue

def move_target_lists_to_queue():
    """Move pending target lists to the queue"""
    # Get all target lists that are pending
    target_lists = TargetList.objects.filter(status='pending')
    
    queue_items_created = 0
    for target_list in target_lists:
        try:
            # Create queue entry
            Queue.objects.create(
                target_list=target_list,
                contact=target_list.contact,
                message=target_list.message,
                userphone=target_list.userphone,
                phone_token=target_list.userphone.phone_token,
                status='pending',
                priority=target_list.priority,  # Use target list priority
                scheduled_time=timezone.now()  # Schedule for immediate processing
            )
            queue_items_created += 1
            
            # Update target list status
            target_list.status = 'processing'
            target_list.save()
            
            print(f"Created queue item for target list {target_list.id} "
                  f"(Contact Type: {target_list.contact_type}, "
                  f"Tag: {target_list.contact_tag}, "
                  f"Phone: {target_list.contact_phone}, "
                  f"Priority: {target_list.priority})")
        except Exception as e:
            print(f"Error processing target list {target_list.id}: {str(e)}")
    
    print(f"\nTotal queue items created: {queue_items_created}")

if __name__ == "__main__":
    move_target_lists_to_queue()