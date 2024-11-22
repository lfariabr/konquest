from django.core.management.base import BaseCommand
from messageShooter.resolvers.target_list_resolver import create_target_list, clean_target_list
from messageShooter.models.queue import Queue
from django.utils import timezone
from messageShooter.models.campaign import Campaign
from datetime import datetime

class Command(BaseCommand):
    help = 'Process a campaign and create target lists'

    def add_arguments(self, parser):
        parser.add_argument('campaign_id', type=int, help='ID of the campaign to process')
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean up old target list entries before processing'
        )

    def handle(self, *args, **options):
        try:
            campaign_id = options['campaign_id']
            
            # Get campaign
            campaign = Campaign.objects.get(id=campaign_id)
            
            if campaign.campaign_status != "Active":
                self.stdout.write(self.style.WARNING(f'Campaign {campaign.name} is not active'))
                return

            # Clean up old entries if requested
            if options['clean']:
                cleaned = clean_target_list()
                if cleaned > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'Cleaned up {cleaned} old target list entries')
                    )

            # Create target list entries
            created, skipped, errors = create_target_list(campaign_id)
            
            if created > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully processed campaign {campaign.name}.\n'
                        f'Created: {created} entries\n'
                        f'Skipped: {skipped} entries\n'
                        f'Errors: {errors} entries'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'No new entries created for campaign {campaign.name}.\n'
                        f'Skipped: {skipped} entries\n'
                        f'Errors: {errors} entries'
                    )
                )

        except Campaign.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Campaign with id {campaign_id} does not exist'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing campaign: {str(e)}')
            )
