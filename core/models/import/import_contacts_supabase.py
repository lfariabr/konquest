import pandas as pd
from supabase import create_client
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
import time

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

def clean_phone(phone):
    """Clean phone number."""
    if not phone:
        return None
    # Remove any non-digit characters
    phone = ''.join(filter(str.isdigit, str(phone)))
    if len(phone) < 8:  # Minimum valid length
        return None
    return phone

def process_contact(row):
    """Process contact details from a row."""
    try:
        phone = clean_phone(row[1])
        if not phone:
            return None

        # Include all required fields with default values
        return {
            "phone": phone,
            "name": str(row[2] or ""),
            "created_at": row[3] if row[3] else datetime.now().isoformat(),
            "relationship_tag": str(row[4] or ""),
            "source": str(row[5] or ""),
            "store": str(row[6] or ""),
            "region": str(row[7] or ""),
            "external_tag": str(row[8] or ""),
            "user_id": int(row[9]) if row[9] else None,
            "is_lead": False,
            # Required fields with default values
            "lead_check_count": 0,
            "lead_status": None,
            "lead_created_at": None,
            "lead_last_checked": None,
            "store_lead": None,
            "is_appointment": False,
            "appointment_id": None,
            "appointment_status": None,
            "appointment_created_at": None,
            "appointment_last_checked": None,
            "appointment_check_count": 0,
            "store_appointment": None,
            "reference_code": None,
            "tag": None,
            "status": None
        }
    except Exception as e:
        logger.error(f"Error processing row: {str(e)}")
        return None

def get_last_processed_row():
    """Get the number of records in the database to determine where to continue from"""
    try:
        response = supabase.table("core_contact").select("*", count="exact").execute()
        return response.count
    except Exception as e:
        logger.error(f"Error getting record count: {str(e)}")
        return 0

def save_progress(offset):
    """Save current progress to a file"""
    with open('import_progress.json', 'w') as f:
        json.dump({'last_offset': offset, 'timestamp': datetime.now().isoformat()}, f)

def load_progress():
    """Load progress from file if it exists"""
    try:
        with open('import_progress.json', 'r') as f:
            data = json.load(f)
            return data['last_offset']
    except:
        return None

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

def import_contacts(sql_file_path, batch_size=25, start_offset=0):
    """Import contacts from SQL file using Supabase client."""
    
    logger.info("Starting contact import...")
    
    # Load previous progress if available
    saved_offset = load_progress()
    if saved_offset and saved_offset > start_offset:
        logger.info(f"Resuming from previous progress: {saved_offset}")
        start_offset = saved_offset
    
    # First, let's verify the table structure
    try:
        logger.info("Verifying table structure...")
        response = supabase.table("core_contact").select("*").limit(1).execute()
        available_columns = response.data[0].keys() if response.data else []
        logger.info(f"Available columns: {available_columns}")
    except Exception as e:
        logger.error(f"Error verifying table structure: {str(e)}")
    
    # Read SQL file
    with open(sql_file_path, 'r') as file:
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

    total_rows = len(values)
    success_count = 0
    error_count = 0
    errors = []

    logger.info(f"Processing {total_rows - start_offset} rows starting from row {start_offset}...")
    
    # Process in batches
    current_offset = start_offset
    while current_offset < total_rows:
        batch_end = min(current_offset + batch_size, total_rows)
        batch = values[current_offset:batch_end]
        
        try:
            # Process batch
            contacts_to_create = []
            for row in batch:
                contact_data = process_contact(row)
                if contact_data:
                    contacts_to_create.append(contact_data)
            
            if contacts_to_create:
                # Insert batch with retry logic
                def insert_batch():
                    return supabase.table("core_contact").insert(contacts_to_create).execute()
                
                result = retry_with_backoff(insert_batch)
                success_count += len(contacts_to_create)
                
                # Save progress every 100 successful inserts
                if success_count % 100 == 0:
                    save_progress(current_offset)
            
            # Print progress
            progress = (current_offset + 1) / total_rows * 100
            logger.info(f"Progress: {current_offset + 1}/{total_rows} - {progress:.1f}%")
            logger.info(f"Successful: {success_count}, Errors: {error_count}")

        except Exception as e:
            error_count += len(batch)
            error_msg = f"Error on batch starting at row {current_offset + 1}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
            
            # Save progress on error
            save_progress(current_offset)
            
            # Small delay before next attempt
            time.sleep(1)

        current_offset = batch_end

    # Final summary
    logger.info("\nImport Complete!")
    logger.info("=================")
    logger.info(f"Total Processed: {total_rows - start_offset}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Errors: {error_count}")
    
    if errors:
        logger.info("\nFirst 10 errors encountered:")
        for error in errors[:10]:
            logger.info(f"- {error}")
        if len(errors) > 10:
            logger.info(f"... and {len(errors) - 10} more errors")

    # Clean up progress file
    if os.path.exists('import_progress.json'):
        os.remove('import_progress.json')

    return success_count

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import contacts from SQL file')
    parser.add_argument('--sql-file', required=True, help='Path to SQL file')
    parser.add_argument('--batch-size', type=int, default=25, help='Number of records to process in each batch')
    parser.add_argument('--start-offset', type=int, default=0, help='Starting offset for resuming interrupted imports')
    
    args = parser.parse_args()
    
    import_contacts(
        sql_file_path=args.sql_file,
        batch_size=args.batch_size,
        start_offset=args.start_offset
    )
