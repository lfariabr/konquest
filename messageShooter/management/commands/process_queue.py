# from django.core.management.base import BaseCommand
# from messageShooter.services.queue_processor import QueueProcessor
# from messageShooter.models import Queue
# import time

# class Command(BaseCommand):
#     help = 'Process messages in the queue'

#     def add_arguments(self, parser):
#         parser.add_argument(
#             '--continuous',
#             action='store_true',
#             help='Run continuously, processing messages as they arrive'
#         )
#         parser.add_argument(
#             '--batch-size',
#             type=int,
#             default=50,
#             help='Number of messages to process in one batch'
#         )
#         parser.add_argument(
#             '--sleep',
#             type=int,
#             default=60,
#             help='Seconds to sleep between batches in continuous mode'
#         )
#         parser.add_argument(
#             '--queue-id',
#             type=int,
#             help='Process a specific queue entry by ID'
#         )

#     def handle(self, *args, **options):
#         queue_id = options.get('queue_id')
#         processor = QueueProcessor()
        
#         # If queue_id is provided, process just that entry
#         if queue_id:
#             try:
#                 # Process specific queue entry
#                 queue_entry = Queue.objects.get(id=queue_id)
#                 success, error = processor.process_queue_item(queue_entry)
#                 queue_entry.refresh_from_db()  # Refresh to get latest status
                
#                 # Show detailed status message
#                 status_color = self.style.SUCCESS if queue_entry.status == 'sent' else self.style.WARNING
#                 status_message = f"Queue entry {queue_id} processed - Status: {queue_entry.status}"
#                 if queue_entry.last_error:
#                     status_message += f" (Error: {queue_entry.last_error})"
                
#                 self.stdout.write(status_color(status_message))
                
#             except Queue.DoesNotExist:
#                 self.stdout.write(
#                     self.style.ERROR(f"Queue entry {queue_id} not found")
#                 )
#             except Exception as e:
#                 self.stdout.write(
#                     self.style.ERROR(f"Error processing queue entry {queue_id}: {str(e)}")
#                 )
#         else:
#             # Process batch of messages
#             batch_size = options['batch_size']
#             continuous = options['continuous']
#             sleep_time = options['sleep']
            
#             while True:
#                 try:
#                     processed, success, errors = processor.process_queue(batch_size=batch_size)
#                     self.stdout.write(
#                         self.style.SUCCESS(
#                             f"Processed {processed} messages ({success} successful, {errors} errors)"
#                         )
#                     )
#                 except Exception as e:
#                     self.stdout.write(
#                         self.style.ERROR(f"Error processing queue: {str(e)}")
#                     )
                
#                 if not continuous:
#                     break
                    
#                 time.sleep(sleep_time)
