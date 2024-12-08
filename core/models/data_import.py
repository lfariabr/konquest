import os
import django
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
CONTACT_FIELD_MAPPING = {
    'phone': 'phone',
    'name': 'name',
    'created_date': 'created_at',
    'tag': 'relationship_tag',
    'source': 'source',
    'store': 'store',
    'region': 'region',
    'user_id': 'user_id',
    'tags': 'external_tag'
}

MESSAGE_LOG_FIELD_MAPPING = {
    'message_text': 'text',
    'user_id': 'user_id',
    'sender_phone_number': 'user_phone',
    'lead_phone_number': 'contact',
    'status': 'status',
    'date_sent': 'sent_at'
}

def clean_phone(phone):
    """Clean phone number by removing non-numeric characters"""
    if not phone:
        return None
    return re.sub(r'\D', '', phone.strip("'"))

def clean_name(name):
    """Clean name by removing quotes and handling null values"""
    if not name or name.lower() == 'null':
        return ''
    return name.strip("'").strip()

def parse_date(date_str):
    """Parse date string to timezone-aware datetime"""
    if not date_str or date_str.lower() == 'null':
        return timezone.now()
    try:
        # Remove quotes and parse date
        clean_date = date_str.strip("'")
        dt = datetime.strptime(clean_date, '%Y-%m-%d %H:%M:%S')
        return timezone.make_aware(dt)
    except Exception as e:
        logger.warning(f"Error parsing date {date_str}: {e}")
        return timezone.now()

def clean_tag(tag):
    """Clean tag by removing quotes and handling null values"""
    if not tag or not isinstance(tag, str):
        return ''
    if tag.lower() == 'null':
        return ''
    return tag.strip("'").strip()

def parse_sql_file(file_path):
    """Parse SQL file and extract values from INSERT statements"""
    logger.info(f"Reading SQL file: {file_path}")
    with open(file_path, 'r') as file:
        content = file.read()
        
    # Find all values in the format ('value1', 'value2', ...)
    pattern = r"\((.*?)\)"
    matches = re.findall(pattern, content)
    values = []
    
    for match in matches:
        # Split by comma but not within quotes
        row_values = []
        current = ''
        in_quotes = False
        
        for char in match:
            if char == "'" and (len(current) == 0 or current[-1] != '\\'):
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                # Clean and add the value
                clean_value = current.strip().strip("'").replace("''", "'")
                row_values.append(clean_value)
                current = ''
            else:
                current += char
                
        # Add the last value
        if current:
            clean_value = current.strip().strip("'").replace("''", "'")
            row_values.append(clean_value)
            
        if row_values:
            # Skip header row
            if not (row_values[0] == '"id"' or row_values[0] == 'id'):
                values.append(row_values)
    
    logger.info(f"Found {len(values)} records")
    if values:
        logger.info(f"Sample record: {values[0]}")  # Log first row as example
        
    return values

def import_contact(data):
    """Import a contact using the defined field mapping"""
    try:
        cleaned_data = {}
        
        # Handle user first since it's required
        user_id = data.get('user_id')
        if not user_id:
            logger.warning("No user_id provided")
            return None
            
        try:
            user_id = int(user_id)
            user = kUser.objects.filter(id=user_id).first()
            if not user:
                # Create user if it doesn't exist
                user = kUser.objects.create(
                    id=user_id,
                    name=f'Imported User {user_id}',
                    email=f'imported_user_{user_id}@imported.com',
                    password=make_password('imported123'),
                    company='Imported Company'
                )
                logger.info(f"Created new user with ID: {user_id}")
            cleaned_data['user'] = user
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id value: {user_id}")
            return None
        
        for legacy_field, new_field in CONTACT_FIELD_MAPPING.items():
            if legacy_field in data:
                value = data[legacy_field]
                
                # Skip empty or null values
                if value in ['null', '', None]:
                    continue
                    
                # Handle special fields
                if legacy_field == 'phone':
                    value = clean_phone(value)
                elif legacy_field == 'name':
                    value = clean_name(value)
                elif legacy_field == 'tag':
                    value = clean_tag(value)
                elif legacy_field == 'tags':
                    value = clean_tag(value)
                elif legacy_field == 'created_date':
                    try:
                        value = parse_date(value) if isinstance(value, str) else value
                    except ValueError as e:
                        logger.warning(f"Error parsing date {legacy_field!r}: {str(e)}")
                        value = timezone.now()
                elif legacy_field == 'user_id':
                    continue  # Skip since we already handled it
                
                cleaned_data[new_field] = value
        
        # Set defaults for required fields if missing
        if 'created_at' not in cleaned_data:
            cleaned_data['created_at'] = timezone.now()
        if 'name' not in cleaned_data or not cleaned_data['name']:
            cleaned_data['name'] = f"Contact {cleaned_data.get('phone', 'Unknown')}"
        
        # Set additional fields
        cleaned_data['is_lead'] = False
            
        return Contact.objects.create(**cleaned_data)
    except Exception as e:
        logger.error(f"Error in import_contact: {str(e)}")
        logger.error(f"Problematic data: {data}")
        return None

def import_message_log(data):
    """Import a message log using the defined field mapping"""
    cleaned_data = {}
    
    for legacy_field, new_field in MESSAGE_LOG_FIELD_MAPPING.items():
        if legacy_field in data:
            value = data[legacy_field]
            if value == 'NULL' or value == '':
                continue
                
            if legacy_field == 'date_sent':
                try:
                    value = parse_date(value)
                except ValueError as e:
                    logger.warning(f"Error parsing date {legacy_field!r}: {str(e)}")
                    continue
            elif legacy_field in ['sender_phone_number', 'lead_phone_number']:
                value = clean_phone(value)
            elif legacy_field == 'user_id':
                try:
                    value = int(value) if value.strip() else None
                except ValueError:
                    logger.warning(f"Invalid user_id value: {value}")
                    continue
            
            cleaned_data[new_field] = value
    
    # Get user first since it's required for Message
    user_id = cleaned_data.pop('user_id', None)
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
                
                # Verify user was saved
                try:
                    saved_user = kUser.objects.get(id=user_id)
                    logger.info(f"Verified saved user: {saved_user.id}, {saved_user.name}")
                except kUser.DoesNotExist:
                    logger.error("Failed to save user - not found after save!")
                    return None
        
        # Create message with user object directly
        with transaction.atomic():  # Nested transaction for message creation
            logger.info(f"Creating message with user {user.id}...")
            try:
                message = Message.objects.create(
                    user=user,
                    text=cleaned_data.pop('text'),
                    title=data.get('message_title', 'Imported Message')
                )
                logger.info(f"Created message with id: {message.id}")
                
                # Verify message was created
                message_check = Message.objects.get(id=message.id)
                logger.info(f"Verified message. User ID: {message_check.user_id}, User: {message_check.user}")
                
                # Add message to cleaned_data for MessageLogs creation
                cleaned_data['message'] = message
                cleaned_data['user'] = user
            except Exception as e:
                logger.error(f"Failed to create message: {str(e)}")
                logger.error(f"User object state: id={user.id}, pk={user.pk}, name={user.name}")
                raise

        # Try to find existing UserPhone
        user_phone_number = cleaned_data.pop('user_phone', None)
        if user_phone_number:
            user_phone = UserPhone.objects.filter(phone_number=user_phone_number).first()
            if user_phone:
                cleaned_data['user_phone'] = user_phone
                cleaned_data['relationship_tag'] = user_phone.relationship_tag
            else:
                # Create UserPhone if it doesn't exist
                user_phone = UserPhone.objects.create(
                    user=user,
                    phone_number=user_phone_number,
                    relationship_tag='imported'
                )
                cleaned_data['user_phone'] = user_phone
                cleaned_data['relationship_tag'] = 'imported'
                logger.info(f"Created new UserPhone for number: {user_phone_number}")
        
        # Try to find existing Contact or create one
        contact_number = cleaned_data.pop('contact', data.get('lead_phone_number'))
        if contact_number:
            contact = Contact.objects.filter(phone=contact_number).first()
            if contact:
                cleaned_data['contact'] = contact
                logger.info(f"Found existing contact: {contact.id}, {contact.phone}")
            else:
                # Create new contact
                contact = Contact.objects.create(
                    phone=contact_number,
                    name=f'Imported Contact {contact_number}',
                    relationship_tag='imported',
                    source='Import',
                    store='CENTRAL',
                    region='São Paulo'
                )
                cleaned_data['contact'] = contact
                logger.info(f"Created new contact: {contact.id}, {contact.phone}")
        else:
            logger.warning("No contact number provided")
        
        return MessageLogs.objects.create(**cleaned_data)
    except Exception as e:
        logger.error(f"Error importing message log: {str(e)}")
        logger.error(f"Problematic data: {data}")
        if 'message' in locals():
            message.delete()  # Clean up created message if log creation fails
        return None

@transaction.atomic
def import_contacts(sql_file_path, limit=25000):
    """Import contacts from SQL file"""
    logger.info("Starting contact import...")
    values = parse_sql_file(sql_file_path)
    imported_count = 0
    
    # Take only the first 'limit' records for testing
    test_values = values[:limit] if limit else values
    logger.info(f"Processing {len(test_values)} out of {len(values)} total records")
    
    for value in test_values:
        try:
            if len(value) < 10:
                logger.warning(f"Skipping record with insufficient values: {value}")
                continue

            data = {
                'phone': value[1],
                'name': value[2],
                'created_date': value[3],
                'tag': value[4],
                'source': value[5],
                'store': value[6],
                'region': value[7],
                'user_id': value[9],
                'tags': value[8]
            }
            
            # Log the data we're about to import
            logger.info(f"Importing contact: {data['phone']} - {data['name']}")
            
            # Check if contact already exists
            existing_contact = Contact.objects.filter(phone=clean_phone(data['phone'])).first()
            if existing_contact:
                logger.info(f"Contact already exists: {existing_contact.phone}")
                continue
                
            # Import the contact
            contact = import_contact(data)
            if contact:
                imported_count += 1
                
            if imported_count % 10 == 0 and imported_count > 0:
                logger.info(f"Imported {imported_count} contacts...")
                
        except Exception as e:
            logger.error(f"Error processing record: {str(e)}")
            logger.error(f"Problematic record: {value}")
            continue
    
    logger.info(f"Successfully imported {imported_count} contacts")
    return imported_count

def run_import():
    """Run the import process"""
    logger.info("Starting import process...")
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        contacts_file = os.path.join(base_dir, 'models', 'leadwhatsapp_rows.sql')
        
        # Only import contacts for now
        import_contacts(contacts_file, limit=25000)  # Test with first 50 contacts
        logger.info("Import process completed successfully!")
    except Exception as e:
        logger.error(f"Import process failed: {str(e)}")
        raise

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konquest.settings')
    django.setup()
    run_import()