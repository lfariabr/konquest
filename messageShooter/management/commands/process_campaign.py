from django.core.management.base import BaseCommand
from messageShooter.models.campaign import Campaign
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue
from core.models.message import Message
from core.models.contact import Contact
from django.utils import timezone
from messageShooter.resolvers.get_counter import get_counter_whatsapp

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

        # Get all target lists for this campaign (removed status filter)
        target_lists = TargetList.objects.filter(
            contact_tag=campaign_tag
        )

        if not target_lists:
            self.stdout.write(self.style.WARNING(f'No target lists found for tag: {campaign_tag}'))
            return

        # Get the message for this counter
        if specific_counter is not None:
            counter = specific_counter
        else:
            # Get the next counter based on sent messages
            counter = get_counter_whatsapp("Whatsapp", campaign_tag)

        message = Message.objects.filter(
            relationship_tag=campaign_tag,
            counter=counter
        ).first()

        if not message:
            self.stdout.write(
                self.style.ERROR(f'No message found for {campaign_tag} with counter {counter}')
            )
            return

        # Create queue entries for each target
        queued_count = 0
        for target in target_lists:
            # Check if queue entry already exists
            existing_queue = Queue.objects.filter(
                target_list=target,
                message=message,
                status__in=['pending', 'processing']
            ).exists()

            if not existing_queue:
                # Get contact - first try the direct relationship, then fallback to reference_id
                contact = target.contact
                if not contact and target.reference_id:
                    try:
                        contact = Contact.objects.get(id=target.reference_id)
                    except (Contact.DoesNotExist, ValueError):
                        self.stdout.write(
                            self.style.ERROR(f'Contact not found for target list {target.id} with reference_id {target.reference_id}')
                        )
                        continue

                if not contact:
                    self.stdout.write(
                        self.style.ERROR(f'No valid contact found for target list {target.id}')
                    )
                    continue

                Queue.objects.create(
                    target_list=target,
                    contact=contact,
                    message=message,
                    userphone=target.userphone,
                    phone_token=target.userphone.phone_token,
                    status='pending',
                    scheduled_time=timezone.now()
                )
                queued_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Created {queued_count} queue entries for {campaign_tag} '
                f'(counter: {counter}, message: {message.title})'
            )
        )
