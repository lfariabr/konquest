# messageShooter/management/commands/run_scheduler.py
# Trigger: python manage.py run_scheduler

from django.core.management.base import BaseCommand
from messageShooter.services.scheduler import CampaignScheduler
from messageShooter.services.queue_processor import QueueProcessor
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run the campaign scheduler service'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-mode',
            action='store_true',
            help='Run in test mode (no sleep)',
        )

    def handle(self, *args, **options):
        """Handle the command execution"""
        self.stdout.write(self.style.SUCCESS("Starting campaign scheduler service..."))
        scheduler = CampaignScheduler()
        queue_processor = QueueProcessor()
        running = True
        test_mode = options.get('test_mode', False)

        try:
            while running:
                try:
                    # Process campaigns
                    self.stdout.write("Processing campaigns...")
                    created_count = scheduler.process_campaigns()
                    self.stdout.write(self.style.SUCCESS(f"Created {created_count} new queue items for campaigns"))

                    if not test_mode:
                        # Process queue
                        self.stdout.write("Processing queue...")
                        processed, success, error = queue_processor.process_queue()
                        self.stdout.write(self.style.SUCCESS(
                            f"Queue processing complete: {processed} processed, {success} successful, {error} errors"
                        ))

                    if test_mode:
                        running = False  # Exit after one iteration in test mode
                    else:
                        time.sleep(60)  # Only sleep in non-test mode
                    
                except Exception as e:
                    error_msg = str(e)
                    if "Campaign processing error" in error_msg:
                        self.stdout.write(self.style.ERROR(f"Error processing campaigns: {error_msg}"))
                    elif "Queue processing error" in error_msg:
                        self.stdout.write(self.style.ERROR(f"Error processing queue: {error_msg}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"Error in scheduler: {error_msg}"))
                    
                    logger.error(error_msg)
                    if test_mode:
                        running = False  # Exit after error in test mode
                    else:
                        time.sleep(60)  # Only sleep in non-test mode
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.stdout.write(self.style.WARNING("\nStopping campaign scheduler service..."))

# TODO: FUTURE IMPROVEMENT
# @app.task
# def check_campaigns():
#     campaign_scheduler = CampaignScheduler()
#     created = campaign_scheduler.process_campaigns()
#     return created


# @app.task
# def process_queue():
#     queue_processor = QueueProcessor()
#     processed, success, errors = queue_processor.process_queue()
#     return processed, success, errors

# # celery_config.py
# from celery.schedules import crontab

# beat_schedule = {
#     'check-campaigns': {
#         'task': 'tasks.check_campaigns',
#         'schedule': 60.0,  # every minute
#     },
#     'process-queue': {
#         'task': 'tasks.process_queue',
#         'schedule': 30.0,  # every 30 seconds
#     }
# }