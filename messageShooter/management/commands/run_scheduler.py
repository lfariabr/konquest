# messageShooter/management/commands/run_scheduler.py
# Trigger: python manage.py run_scheduler

from django.core.management.base import BaseCommand
from messageShooter.services.queue_processor import QueueProcessor
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run the campaign scheduler service'

    def add_arguments(self, parser):
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Run continuously',
        )
        parser.add_argument(
            '--sleep',
            type=int,
            default=60, # every minute
            help='Sleep time in seconds',
        )
        parser.add_argument(
            '--max-iterations',
            type=int,
            default=None,
            help='Maximum number of iterations (for testing)',
        )
        parser.add_argument(
            '--test-mode',
            action='store_true',
            help='Run in test mode (for testing)',
        )

    def handle(self, *args, **options):
        """Run the scheduler"""
        continuous = options['continuous']
        sleep_time = options['sleep']
        max_iterations = options['max_iterations']
        test_mode = options['test_mode']
        queue_processor = QueueProcessor()
        from messageShooter.services.scheduler import CampaignScheduler
        campaign_scheduler = CampaignScheduler()
        iterations = 0

        while True:
            try:
                # Process campaigns first
                self.stdout.write("Starting campaign processing")
                campaign_scheduler.process_campaigns()

                # Then process queue
                self.stdout.write("Starting queue processing")
                processed, success, error = queue_processor.process_queue()
                if processed > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Processed {processed} messages ({success} successful, {error} errors)"
                        )
                    )

                # Check if we should continue
                iterations += 1
                if not continuous or (max_iterations and iterations >= max_iterations):
                    break
                    
                time.sleep(sleep_time)

            except KeyboardInterrupt:
                self.stdout.write(
                    self.style.ERROR("Error in scheduler: KeyboardInterrupt")
                )
                break
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error in scheduler: {str(e)}")
                )
                break

        # Final status message
        if continuous:
            self.stdout.write(self.style.SUCCESS("Scheduler stopped"))