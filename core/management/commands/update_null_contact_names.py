# I need to create a command to grab Phone Number from contacts that name == "null", match them with the Appointment customer phone number and update them (only the name, of course...) back to the contacs model, so we have it all updated...

# I have had a problem where I client was called "Null" on the salutation... hahaha, fuck that happens when you're fuck building the airplane while it is midflight type of thing, right?

from django.core.management.base import BaseCommand
from django.db.models import Q
from core.models.contact import Contact
from apiCrm.models.appointment import Appointment
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Update contact names that are null with corresponding appointment customer name."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run the command without actually making changes.',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of contacts to process in each batch.',
        )
    
    def handle(self, *args, **options):
        try:
            dry_run = options['dry_run']
            batch_size = options['batch_size']
            
            # Find all contacts with null names using Q objects
            null_contacts = Contact.objects.filter(
                Q(name__isnull=True) |
                Q(name__iexact='null') |
                Q(name__exact='') |
                Q(name__iexact='undefined')
            )
            
            total_contacts = null_contacts.count()
            logger.info(f"Found {total_contacts} contacts with null names")
            
            updated_count = 0
            not_found_count = 0
            processed_count = 0
            
            # Process in batches
            while processed_count < total_contacts:
                batch = null_contacts[processed_count:processed_count + batch_size]
                
                for contact in batch:
                    try:
                        # Find matching appointment by phone number
                        matching_appointment = Appointment.objects.filter(
                            customer_phone=contact.phone
                        ).order_by('-createdby_created_at').first()
                        
                        if matching_appointment:
                            old_name = contact.name or 'None'
                            new_name = matching_appointment.customer_name
                            
                            if not dry_run:
                                contact.name = new_name
                                contact.save(update_fields=['name'])
                                
                            logger.info(
                                f"Updated contact {contact.phone}: "
                                f"'{old_name}' -> '{new_name}' "
                                f"(Appointment ID: {matching_appointment.id})"
                            )
                            updated_count += 1
                        else:
                            logger.warning(
                                f"No matching appointment found for contact {contact.phone}"
                            )
                            not_found_count += 1
                    except Exception as e:
                        logger.error(f"Error updating contact {contact.phone}: {str(e)}")
                
                processed_count += batch_size
                logger.info(f"Processed {min(processed_count, total_contacts)}/{total_contacts} contacts")
                
            # Summary:
            action = "Would update" if dry_run else "Updated"
            logger.info(
                f"\nSummary:\n"
                f"Total null contacts: {total_contacts}\n"
                f"{action}: {updated_count}\n"
                f"Not found: {not_found_count}"
            )

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        "This was a dry run. No changes were made. "
                        "Run without --dry-run to apply changes."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully updated {updated_count} contact names"
                    )
                )
        
        except Exception as e:
            logger.error(f"Command failed: {str(e)}")
            raise