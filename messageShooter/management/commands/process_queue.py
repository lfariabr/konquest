from django.core.management.base import BaseCommand
from messageShooter.resolvers.queue_resolver import process_queue
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

    def handle(self, *args, **options):
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
