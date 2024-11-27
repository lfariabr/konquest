from django.core.management.base import BaseCommand
from messageShooter.resolvers.queue_resolver import process_queue, process_queue_by_id
import time

class Command(BaseCommand):
    help = 'Process messages in the queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Run continuously, processing messages as they arrive'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of messages to process in one batch'
        )
        parser.add_argument(
            '--sleep',
            type=int,
            default=60,
            help='Seconds to sleep between batches in continuous mode'
        )
        parser.add_argument(
            '--queue-id',
            type=int,
            help='Process a specific queue entry by ID'
        )

    def handle(self, *args, **options):
        queue_id = options.get('queue_id')
        
        # If queue_id is provided, process just that entry
        if queue_id:
            try:
                success = process_queue_by_id(queue_id)
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully processed queue entry {queue_id}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to process queue entry {queue_id}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing queue entry {queue_id}: {str(e)}')
                )
            return

        # Otherwise, process in batch mode
        continuous = options['continuous']
        batch_size = options['batch_size']
        sleep_time = options['sleep']

        while True:
            try:
                processed, success, errors = process_queue(batch_size=batch_size)
                
                if processed > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Processed {processed} messages: {success} successful, {errors} errors'
                        )
                    )
                else:
                    self.stdout.write('No messages to process')

                if not continuous:
                    break

                time.sleep(sleep_time)

            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nStopping queue processor'))
                break
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing queue: {str(e)}')
                )
                if not continuous:
                    raise
