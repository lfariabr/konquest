import logging
from celery import shared_task
from django.db import connection, transaction
from django.db.models import ProtectedError
from apiCrm.models.lead import Lead
from apiCrm.models.appointment import Appointment
from apiCrm.models.billcharge import BillCharge
from core.models.contact import Contact
from django.utils import timezone
from datetime import timedelta, datetime
from django.utils import timezone
from django.conf import settings
from decouple import config
from apiCrm.schemas.resolve_all_data import fetch_data, process_leads_batch, process_appointments_batch, process_bill_charges_batch

token = config('TOKEN')

logger = logging.getLogger(__name__)

@shared_task(
    name='apiCrm.cleanup_crm_tables',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=27000 # 450 minutes
)
def cleanup_crm_tables():
    """
    Daily task to clean up CRM-related tables with proper dependency handling.
    Uses PostgreSQL-specific syntax for cleanup while maintaining referential integrity.
    """
    logger.info("Starting CRM tables cleanup")
    
    try:
        with connection.cursor() as cursor:
            # Check if tables exist first
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('apiCrm_billcharge', 'apiCrm_appointment', 'apiCrm_lead')
                );
            """)
            tables_exist = cursor.fetchone()[0]
            
            if not tables_exist:
                logger.warning("One or more CRM tables do not exist. Skipping cleanup.")
                return False
            
            try:
                with transaction.atomic():
                    # Try to clean each table individually to handle partial existence
                    for table in ['apiCrm_billcharge', 'apiCrm_appointment', 'apiCrm_lead']:
                        try:
                            cursor.execute('TRUNCATE TABLE "%s" CASCADE;' % table)
                            logger.info(f"Successfully truncated {table}")
                        except Exception as e:
                            logger.warning(f"Could not truncate {table}: {str(e)}")
                    
                    # Log final table counts
                    cursor.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'apiCrm_billcharge') as billcharges_exists,
                            (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'apiCrm_appointment') as appointments_exists,
                            (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'apiCrm_lead') as leads_exists;
                    """)
                    counts = cursor.fetchone()
                    logger.info(f"Table existence check: {counts}")
                    
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")
                raise
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to clean CRM tables: {str(e)}", exc_info=True)
        raise

# This task should be triggered right after apiCrm.fetch_all_data when it's implemented
@shared_task(
    name='apiCrm.check_contacts_in_crm',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=27000 # 45 minutes
)
def check_contacts_in_crm():
    """
    Task to check if contacts exist in CRM tables.
    Processes contacts and tracks progress.
    
    Returns:
        dict: Statistics about the check operation
    """
    logger.info("Starting contact check in CRM")
    stats = {
        'total_contacts': 0,
        'leads_found': 0,
        'appointments_found': 0,
        'billcharges_found': 0,
        'errors': 0,
        'start_time': timezone.now()
    }
    
    try:
        # Get most recent contacts
        contacts = Contact.objects.all().order_by('-id')[:2000]
        total_contacts = len(contacts)
        stats['total_contacts'] = total_contacts
        
        for idx, contact in enumerate(contacts, 1):
            progress = (idx / total_contacts) * 100
            logger.info(f"Processing contact {idx}/{total_contacts} ({progress:.1f}%) - {contact.phone}")
            
            try:
                with transaction.atomic():
                    # Check if contact exists as lead and update tracking
                    lead = contact.check_if_lead_exists()
                    if lead:
                        stats['leads_found'] += 1
                    
                    # Check if contact exists as appointment and update tracking
                    appointment = contact.check_if_appointment_exists()
                    if appointment:
                        stats['appointments_found'] += 1
                    
                    # Check if contact exists as billcharge and update tracking
                    billcharge = contact.check_if_bill_charges_exists()
                    if billcharge:
                        stats['billcharges_found'] += 1

            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error processing contact {contact.id}: {str(e)}", exc_info=True)
                continue
        
        # Calculate final statistics
        stats['end_time'] = timezone.now()
        duration = (stats['end_time'] - stats['start_time']).total_seconds()
        
        logger.info(
            "Contact check completed:\n"
            f"- Processed: {stats['total_contacts']} contacts\n"
            f"- Found: {stats['leads_found']} leads, {stats['appointments_found']} appointments, {stats['billcharges_found']} billcharges\n"
            f"- Errors: {stats['errors']}\n"
            f"- Duration: {duration:.2f} seconds"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to check contacts in CRM: {str(e)}", exc_info=True)
        raise

# This task should be triggered right after cleanup_crm_tables
from apiCrm.schemas.resolve_all_data import Query

@shared_task(
    name='apiCrm.fetch_all_data',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=27000,
    rate_limit='1/h'
)
def fetch_all_data():
    """
    Fetch all CRM data for the last 30 days and upcoming 15 days.
    This task should run after cleanup_crm_tables and before check_contacts_in_crm.
    """
    today = datetime.now().date()
    start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    extended_end_date = (today + timedelta(days=20)).strftime('%Y-%m-%d')

    try:
        logger.info(f"Fetching data for dates: {start_date} to {extended_end_date}")
        
        # Use the same resolver as the GraphQL endpoint
        query = Query()
        result = query.resolve_all_data(None, start_date, end_date, extended_end_date)
        
        # Return counts instead of GraphQL types
        stats = {
            'leads_count': len(result.leads) if result.leads else 0,
            'appointments_count': len(result.appointments) if result.appointments else 0,
            'bill_charges_count': len(result.bill_charges) if result.bill_charges else 0,
            'date_range': f"{start_date} to {extended_end_date}"
        }
        
        logger.info(f"Successfully fetched and processed data")
        return stats
        
    except Exception as e:
        logger.error(f"Error in fetch_all_data: {str(e)}", exc_info=True)
        raise