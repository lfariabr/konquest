import logging
import re
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import time
from supabase import create_client
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Supabase configuration
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

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
        # First try to parse as Unix timestamp
        if str(date_str).isdigit():
            try:
                # Convert to seconds if in milliseconds
                timestamp = int(date_str)
                if timestamp > 9999999999:  # If in milliseconds
                    timestamp = timestamp / 1000
                return datetime.fromtimestamp(timestamp).isoformat()
            except (ValueError, OSError) as e:
                logger.warning(f"Failed to parse Unix timestamp {date_str}: {e}")
                pass

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
                return dt.isoformat()
            except ValueError:
                continue
        raise ValueError(f"Could not parse date: {date_str}")
    except Exception as e:
        raise ValueError(f"Error parsing date {date_str}: {str(e)}")

def retry_with_backoff(func, max_retries=3):
    """Retry a function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                raise e
            wait_time = (2 ** attempt) + 1  # Exponential backoff
            logger.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

def simple_hash_password(password):
    """Simple password hashing without Django dependencies"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_or_create_user(user_id):
    """Get or create a user in Supabase"""
    try:
        # Try to get existing user
        response = supabase.table("core_kuser").select("*").eq("id", user_id).execute()
        if response.data:
            logger.info(f"Found existing user: {user_id}")
            return response.data[0]
        
        # Create new user if not exists
        logger.info(f"Creating new user with id {user_id}")
        user_data = {
            "id": user_id,
            "name": f'Imported User {user_id}',
            "email": f'imported_user_{user_id}@imported.com',
            "password": simple_hash_password('imported123'),
            "created_at": datetime.now().isoformat()
        }
        response = supabase.table("core_kuser").insert(user_data).execute()
        logger.info(f"Created user: {user_id}")
        return response.data[0]
    except Exception as e:
        logger.error(f"Failed to handle user: {str(e)}")
        return None

def get_or_create_message(user_id, text, title):
    """Create a message in Supabase"""
    try:
        message_data = {
            "user_id": user_id,  # Changed from user to user_id to match Supabase schema
            "text": text,
            "title": title,
            "counter": 1,  # Required field
            "created_at": datetime.now().isoformat()  # Add creation timestamp
        }
        response = supabase.table("core_message").insert(message_data).execute()
        logger.info(f"Created message")
        return response.data[0]
    except Exception as e:
        logger.error(f"Failed to create message: {str(e)}")
        return None

def get_or_create_user_phone(user_id, phone_number):
    """Get or create a user phone in Supabase"""
    try:
        if not phone_number:
            return None
            
        # Check if phone exists
        response = supabase.table("core_userphone").select("*").eq("phone_number", phone_number).execute()
        if response.data:
            return response.data[0]
            
        # Create new phone
        phone_data = {
            "user_id": user_id,
            "phone_number": phone_number,
            "relationship_tag": "imported"
        }
        response = supabase.table("core_userphone").insert(phone_data).execute()
        logger.info(f"Created new UserPhone for number: {phone_number}")
        return response.data[0]
    except Exception as e:
        logger.warning(f"Failed to handle UserPhone: {str(e)}")
        return None

def get_or_create_contact(user_id, phone_number):
    """Get or create a contact in Supabase"""
    try:
        if not phone_number:
            return None
            
        # Check if contact exists
        response = supabase.table("core_contact").select("*").eq("phone", phone_number).execute()
        if response.data:
            return response.data[0]
            
        # Create new contact
        contact_data = {
            "user_id": user_id,
            "phone": phone_number,
            "name": f"Contact {phone_number}",
            "created_at": datetime.now().isoformat(),
            "lead_check_count": 0,
            "appointment_check_count": 0,
            "is_lead": False,
            "is_appointment": False
        }
        response = supabase.table("core_contact").insert(contact_data).execute()
        logger.info(f"Created new Contact for number: {phone_number}")
        return response.data[0]
    except Exception as e:
        logger.warning(f"Failed to handle Contact: {str(e)}")
        return None

def import_message_log(data):
    """Import a message log using Supabase"""
    try:
        # Get user first since it's required
        user_id = data.get('user_id')
        if not user_id:
            logger.warning("Skipping message log - no user_id provided")
            return None
            
        # Get or create user
        user = get_or_create_user(user_id)
        if not user:
            return None

        # Create message
        message_data = {
            "user_id": user['id'],  # Changed back to user_id for Supabase schema
            "text": data.get('message_text', ''),
            "title": data.get('message_title', 'Imported Message'),
            "counter": 1,  # Required field
            "created_at": datetime.now().isoformat()
        }
        message = None
        try:
            response = supabase.table("core_message").insert(message_data).execute()
            message = response.data[0]
            logger.info(f"Created message with id: {message['id']}")
        except Exception as e:
            logger.error(f"Failed to create message: {str(e)}")
            return None

        # Process UserPhone
        user_phone = None
        phone_number = clean_phone(data.get('sender_phone_number'))
        if phone_number:
            user_phone = get_or_create_user_phone(user['id'], phone_number)

        # Process Contact
        contact = None
        contact_number = clean_phone(data.get('lead_phone_number'))
        if contact_number:
            contact = get_or_create_contact(user['id'], contact_number)

        # Create MessageLog
        try:
            status = data.get('status', 'sent')
            sent_at = parse_date(data.get('date_sent'))
            if not sent_at:
                logger.warning("No date_sent provided for message log")
                return None

            relationship_tag = user_phone['relationship_tag'] if user_phone else ''

            message_log_data = {
                "message_id": message['id'],  # ForeignKey to Message
                "user_id": user['id'],        # ForeignKey to kUser
                "user_phone_id": user_phone['id'] if user_phone else None,  # ForeignKey to UserPhone
                "contact_id": contact['id'] if contact else None,           # ForeignKey to Contact
                "status": status,             # CharField
                "sent_at": sent_at,           # DateTimeField
                "relationship_tag": relationship_tag or ''  # CharField with default=''
            }
            
            response = supabase.table("core_messagelogs").insert(message_log_data).execute()
            logger.info(f"Created MessageLog")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create MessageLog: {str(e)}")
            return None

    except Exception as e:
        logger.error(f"Error in import_message_log: {str(e)}")
        logger.error(f"Problematic data: {data}")
        return None

def save_progress(offset):
    """Save current progress to a file"""
    with open('import_messages_progress.json', 'w') as f:
        json.dump({'last_offset': offset, 'timestamp': datetime.now().isoformat()}, f)

def load_progress():
    """Load progress from file if it exists"""
    try:
        with open('import_messages_progress.json', 'r') as f:
            data = json.load(f)
            return data['last_offset']
    except:
        return None

def import_message_logs(data_list, batch_size=25, start_offset=0, limit=35000):
    """Import multiple message logs"""
    if limit:
        data_list = data_list[:limit]
    
    # Load previous progress if available
    saved_offset = load_progress()
    if saved_offset and saved_offset > start_offset:
        logger.info(f"Resuming from previous progress: {saved_offset}")
        start_offset = saved_offset
    
    total_count = len(data_list)
    success_count = 0
    error_count = 0
    
    logger.info(f"Starting import of {total_count} message logs...")
    
    current_offset = start_offset
    while current_offset < total_count:
        batch_end = min(current_offset + batch_size, total_count)
        batch = data_list[current_offset:batch_end]
        
        for data in batch:
            try:
                result = import_message_log(data)
                if result:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing message log: {str(e)}")
        
        # Save progress
        save_progress(current_offset)
        
        # Print progress
        progress = (current_offset + 1) / total_count * 100
        logger.info(f"Progress: {current_offset + 1}/{total_count} - {progress:.1f}%")
        logger.info(f"Successful: {success_count}, Errors: {error_count}")
        
        current_offset = batch_end
    
    logger.info("\nImport Complete!")
    logger.info("=================")
    logger.info(f"Total Processed: {total_count}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Errors: {error_count}")
    
    # Clean up progress file
    if os.path.exists('import_messages_progress.json'):
        os.remove('import_messages_progress.json')
    
    return success_count

def run_import(limit=35000):
    """Main function to run the import process"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import message logs from SQL file')
    parser.add_argument('--sql-file', required=True, help='Path to SQL file')
    parser.add_argument('--batch-size', type=int, default=25, help='Number of records to process in each batch')
    parser.add_argument('--start-offset', type=int, default=0, help='Starting offset for resuming interrupted imports')
    parser.add_argument('--limit', type=int, default=limit, help='Maximum number of records to process')
    
    args = parser.parse_args()
    
    # Read SQL file
    with open(args.sql_file, 'r') as file:
        content = file.read()
        values_start = content.find('VALUES')
        if values_start == -1:
            logger.error("No VALUES found in SQL file")
            return
        
        values_content = content[values_start:].strip()
        values = []
        current_value = []
        in_parentheses = 0
        current_str = ""
        
        for char in values_content:
            if char == '(':
                in_parentheses += 1
            elif char == ')':
                in_parentheses -= 1
                if in_parentheses == 0:
                    current_value.append(current_str.strip())
                    values.append(tuple(v.strip("'") for v in current_value))
                    current_value = []
                    current_str = ""
            elif char == ',' and in_parentheses == 1:
                current_value.append(current_str.strip())
                current_str = ""
            else:
                current_str += char
    
    # Convert values to list of dictionaries
    data_list = []
    for value in values:
        try:
            # Assuming the SQL file columns are in this order:
            # id, phone, message, created_at, status, user_id, ...
            data = {
                'message_text': value[2] if len(value) > 2 else '',
                'user_id': int(value[5]) if len(value) > 5 and value[5] and value[5].isdigit() else None,  # Make sure user_id is an integer
                'sender_phone_number': value[1] if len(value) > 1 else None,
                'lead_phone_number': value[1] if len(value) > 1 else None,
                'status': value[4] if len(value) > 4 else 'sent',
                'date_sent': value[3] if len(value) > 3 else None,
                'message_title': 'Imported Message'
            }
            # Only add if we have a valid user_id
            if data['user_id'] is not None:
                data_list.append(data)
            else:
                logger.warning(f"Skipping row due to invalid user_id: {value}")
        except Exception as e:
            logger.warning(f"Error processing row {value}: {str(e)}")
            continue
    
    return import_message_logs(
        data_list,
        batch_size=args.batch_size,
        start_offset=args.start_offset,
        limit=args.limit
    )

if __name__ == '__main__':
    run_import()
