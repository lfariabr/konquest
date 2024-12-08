import logging
import re
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.hashers import make_password
from core.models.contact import Contact
from core.models.messagelog import MessageLogs
from core.models.user import kUser
from core.models.message import Message
from core.models.userphone import UserPhone

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Field mappings from legacy to current schema
MESSAGE_LOG_FIELD_MAPPING = {
    'message_text': 'text',
    'user_id': 'user_id',
    'sender_phone_number': 'user_phone',
    'lead_phone_number': 'contact',
    'status': 'status',
    'date_sent': 'sent_at',
    'message_title': 'title'
}

def clean_phone(phone):
    """Clean phone number by removing non-numeric characters"""
    if not phone:
        return None
    return re.sub(r'\D', '', str(phone))

def parse_date(date_str):
    """Parse date string to datetime object"""
    if not date_str:
        return None
    try:
        # Try different date formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y'
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return timezone.make_aware(dt)
            except ValueError:
                continue
        raise ValueError(f"Could not parse date: {date_str}")
    except Exception as e:
        raise ValueError(f"Error parsing date {date_str}: {str(e)}")

def import_message_log(data):
    """Import a message log using the defined field mapping"""
    try:
        cleaned_data = {}
        
        # Get user first since it's required for Message
        user_id = data.get('user_id')
        if not user_id:
            logger.warning("Skipping message log - no user_id provided")
            return None
            
        # Try to get or create user explicitly
        try:
            with transaction.atomic():  # Nested transaction for user creation
                user_id = int(user_id)  # Ensure it's an integer
                logger.info(f"Looking for user with id {user_id}")
                
                try:
                    user = kUser.objects.get(id=user_id)
                    logger.info(f"Found existing user: {user.id}")
                except kUser.DoesNotExist:
                    logger.info(f"Creating new user with id {user_id}")
                    user = kUser(
                        id=user_id,
                        name=f'Imported User {user_id}',
                        email=f'imported_user_{user_id}@imported.com',
                        password=make_password('imported123'),
                        company='Imported Company'
                    )
                    user.save()
                    logger.info(f"Created user: {user.id}, {user.name}, {user.email}")
        except Exception as e:
            logger.error(f"Failed to handle user: {str(e)}")
            return None

        # Create message with user object
        try:
            with transaction.atomic():
                message_text = data.get('message_text', '')
                message_title = data.get('message_title', 'Imported Message')
                
                message = Message.objects.create(
                    user=user,
                    text=message_text,
                    title=message_title
                )
                logger.info(f"Created message with id: {message.id}")
        except Exception as e:
            logger.error(f"Failed to create message: {str(e)}")
            return None

        # Process UserPhone
        user_phone = None
        phone_number = clean_phone(data.get('sender_phone_number'))
        if phone_number:
            try:
                user_phone = UserPhone.objects.filter(phone_number=phone_number).first()
                if not user_phone:
                    user_phone = UserPhone.objects.create(
                        user=user,
                        phone_number=phone_number,
                        relationship_tag='imported'
                    )
                    logger.info(f"Created new UserPhone for number: {phone_number}")
            except Exception as e:
                logger.warning(f"Failed to handle UserPhone: {str(e)}")

        # Process Contact
        contact = None
        contact_number = clean_phone(data.get('lead_phone_number'))
        if contact_number:
            try:
                contact = Contact.objects.filter(phone=contact_number).first()
                if not contact:
                    contact = Contact.objects.create(
                        phone=contact_number,
                        name=f"Contact {contact_number}",
                        user=user
                    )
                    logger.info(f"Created new Contact for number: {contact_number}")
            except Exception as e:
                logger.warning(f"Failed to handle Contact: {str(e)}")

        # Create MessageLog
        try:
            status = data.get('status', 'sent')
            sent_at = parse_date(data.get('date_sent'))
            if not sent_at:
                logger.warning("No date_sent provided for message log")
                return None
            relationship_tag = user_phone.relationship_tag if user_phone else ''

            # Create MessageLog instance but don't save it yet
            message_log = MessageLogs(
                message=message,
                user=user,
                user_phone=user_phone,
                contact=contact,
                status=status,
                sent_at=sent_at,  # Set the sent_at field
                relationship_tag=relationship_tag
            )
            
            # Use a raw SQL query to insert the record with our custom sent_at
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO core_messagelogs 
                    (message_id, user_id, user_phone_id, contact_id, status, sent_at, relationship_tag)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, [
                    message.id,
                    user.id,
                    user_phone.id if user_phone else None,
                    contact.id if contact else None,
                    status,
                    sent_at,
                    relationship_tag
                ])
                message_log.id = cursor.fetchone()[0]
            
            logger.info(f"Created MessageLog: {message_log.id}")
            return message_log
        except Exception as e:
            logger.error(f"Failed to create MessageLog: {str(e)}")
            return None

    except Exception as e:
        logger.error(f"Error in import_message_log: {str(e)}")
        logger.error(f"Problematic data: {data}")
        return None

def import_message_logs(data_list, limit=1500):
    """Import multiple message logs"""
    if limit:
        data_list = data_list[:limit]
    
    success_count = 0
    total_count = len(data_list)
    
    logger.info(f"Starting import of {total_count} message logs...")
    
    for idx, data in enumerate(data_list, 1):
        try:
            if import_message_log(data):
                success_count += 1
            
            if idx % 100 == 0:
                logger.info(f"Processed {idx}/{total_count} message logs...")
                
        except Exception as e:
            logger.error(f"Failed to import message log {idx}: {str(e)}")
            continue
    
    logger.info(f"Successfully imported {success_count} out of {total_count} message logs")
    return success_count

def run_import(limit=1500):
    """Main function to run the import process"""
    import os
    
    # Get the SQL file path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(current_dir, 'message_logs_rows.sql')
    
    logger.info("Starting message logs import...")
    logger.info(f"Reading SQL file: {sql_file}")
    
    try:
        with open(sql_file, 'r') as f:
            content = f.read()
            
        # Extract values from INSERT statements
        records = []
        # Split by VALUES to get the actual data part
        parts = content.split('VALUES')
        if len(parts) > 1:
            # Get the values part
            values_part = parts[1]
            # Split into individual records
            value_groups = values_part.split('), (')
            
            for group in value_groups:
                # Clean up the group
                group = group.strip('();').strip('(').strip(')')
                # Split values and clean them
                values = []
                current_value = ''
                in_quotes = False
                
                for char in group:
                    if char == "'" and (len(current_value) == 0 or current_value[-1] != '\\'):
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        cleaned_value = current_value.strip().strip("'").strip()
                        values.append(cleaned_value if cleaned_value != 'null' else None)
                        current_value = ''
                    else:
                        current_value += char
                
                # Don't forget the last value
                if current_value:
                    cleaned_value = current_value.strip().strip("'").strip()
                    values.append(cleaned_value if cleaned_value != 'null' else None)
                
                if len(values) >= 12:  # Ensure we have all required fields
                    record = {
                        'id': values[0],
                        'message_id': values[1],
                        'sender_phone_id': values[2],
                        'sender_phone_number': values[3],
                        'source': values[4],
                        'lead_phone_id': values[5],
                        'lead_phone_number': values[6],
                        'date_sent': values[7],
                        'status': values[8],
                        'message_text': values[9],
                        'message_title': values[10],
                        'user_id': values[11]
                    }
                    records.append(record)
                    logger.info(f"Parsed record: ID={record['id']}, Phone={record['sender_phone_number']}")
        
        logger.info(f"Found {len(records)} records")
        return import_message_logs(records, limit)
        
    except FileNotFoundError:
        logger.error(f"SQL file not found: {sql_file}")
        return 0
    except Exception as e:
        logger.error(f"Error running import: {str(e)}")
        logger.exception(e)  # Log the full traceback
        return 0

if __name__ == '__main__':
    run_import()
