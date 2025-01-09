# open pyshell on a beautiful interface
python manage.py shell

# 1. Clean up CRM tables
from apiCrm.tasks import cleanup_crm_tables
cleanup_crm_tables()

# 2. Run the campaign processing
from apiCrm.tasks import process_scheduled_campaigns
process_scheduled_campaigns()

# 3. Check Queue Results
from messageShooter.models.queue import Queue
from django.db.models import Count

queues = Queue.objects.values(
    'campaign__name',
    'status',
    'total_contacts',
    'processed_count'
).order_by('campaign__name')

print("\nQueue Details:")
for queue in queues:
    print(f"\nCampaign: {queue['campaign__name']}")
    print(f"Status: {queue['status']}")
    print(f"Total Contacts: {queue['total_contacts']}")
    print(f"Processed: {queue['processed_count']}")