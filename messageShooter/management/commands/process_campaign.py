from django.utils import timezone
from core.models.message import Message
from core.models.contact import Contact
from messageShooter.models.queue import Queue
from messageShooter.models.campaign import Campaign
from messageShooter.models.target_list import TargetList
from messageShooter.resolvers.get_counter import get_counter_whatsapp
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Process campaign messages sequentially'

    def add_arguments(self, parser):
        parser.add_argument(
            'campaign_tag',
            type=str,
            help='Campaign tag to process (e.g., "Botox")'
        )
        parser.add_argument(
            '--counter',
            type=int,
            help='Specific counter to process. If not provided, uses next available counter.'
        )

    def handle(self, *args, **options):
        campaign_tag = options['campaign_tag']
        specific_counter = options.get('counter')

        # Get active campaign
        campaign = Campaign.objects.filter(
            contact_tag=campaign_tag,
            campaign_status='Active'
        ).first()

        if not campaign:
            self.stdout.write(self.style.ERROR(f'No active campaign found for tag: {campaign_tag}'))
            return

        # Process the campaign
        success, message = campaign.process_campaign()
        
        if success:
            self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stdout.write(self.style.ERROR(message))
