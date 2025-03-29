"""
Script to send debug notifications to UserPhone dict:
python scripts/x9.py
"""
import os
import sys
import django
from typing import List, Tuple, Dict, Any

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konquist.settings')
django.setup()

import logging
from messageShooter.tasks.campaign_tasks import send_debug_notification
from apiSocialHub.resolvers.send_text_message import send_text_message
from messageShooter.services.email_alert import send_invalid_token_notification
from apiSocialHub.resolvers.monitor import monitor_api_response
from core.models.userphone import UserPhone
from konquist.settings import ADMIN_PHONE

"""
This script validates phone tokens by attempting to send test messages.
It processes UserPhone records in batches, monitors for invalid tokens,
and notifies the team about any issues found.
"""

# Configure logging to also print to console
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

BATCH_SIZE = 100
TEST_MESSAGE = "API Token Validation Test"

def validate_api_response(response: Dict[str, Any]) -> bool:
    """
    Validate if the API response indicates a valid token.
    
    Args:
        response: API response dictionary
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    if not isinstance(response, dict):
        logger.error(f"Unexpected response type: {type(response)}")
        return False
        
    success = response.get('success', False)
    message = response.get('message', '').lower()
    
    return success and 'invalid api_token' not in message

def process_batch(phones: List[UserPhone]) -> List[Tuple[str, str]]:
    """
    Process a batch of phone numbers and return invalid tokens.
    
    Args:
        phones: List of UserPhone objects to validate
        
    Returns:
        List of tuples containing (phone_number, token) for invalid tokens
    """
    invalid_tokens = []
    
    # for userphone in phones:
    #     try:
    #         logger.info(f"Testing token for phone {userphone.phone_number}")
    #         print(f"🔍 Testing token for phone {userphone.phone_number}...")
            
    #         response = send_text_message(
    #             ADMIN_PHONE,
    #             TEST_MESSAGE,
    #             userphone.phone_token,
    #             userphone.relationship_tag
    #         )
            
    #         if not validate_api_response(response):
    #             logger.warning(
    #                 f"Invalid token detected for phone: {userphone.phone_number}",
    #                 extra={
    #                     'phone': userphone.phone_number,
    #                     'token': userphone.phone_token,
    #                     'response': response
    #                 }
    #             )
    #             print(f"❌ Invalid token found for {userphone.phone_number}")
    #             invalid_tokens.append((userphone.phone_number, userphone.phone_token))
    #             monitor_api_response(
    #                 userphone.phone_number,
    #                 userphone.phone_token,
    #                 response
    #             )
    #         else:
    #             logger.info(f"Valid token confirmed for phone: {userphone.phone_number}")
    #             print(f"✅ Valid token for {userphone.phone_number}")
                
    #     except Exception as e:
    #         logger.error(
    #             f"Error processing phone {userphone.phone_number}",
    #             exc_info=True,
    #             extra={'phone': userphone.phone_number}
    #         )
    #         print(f"❌ Error processing {userphone.phone_number}: {str(e)}")
            
    # return invalid_tokens

    # Filter phones to only include those in the failing_phones_to_try list
    filtered_phones = [phone for phone in phones if phone.phone_number in failing_phones_to_try]
    
    print(f"Processing {len(filtered_phones)} phones from the failing phones list...")
    
    for userphone in filtered_phones:
        try:
            logger.info(f"Testing token for phone {userphone.phone_number}")
            print(f"🔍 Testing token for phone {userphone.phone_number}...")
            
            response = send_text_message(
                ADMIN_PHONE,
                TEST_MESSAGE,
                userphone.phone_token,
                userphone.relationship_tag
            )
            
            if not validate_api_response(response):
                logger.warning(
                    f"Invalid token detected for phone: {userphone.phone_number}",
                    extra={
                        'phone': userphone.phone_number,
                        'token': userphone.phone_token,
                        'response': response
                    }
                )
                print(f"❌ Invalid token found for {userphone.phone_number}")
                invalid_tokens.append((userphone.phone_number, userphone.phone_token))
                monitor_api_response(
                    userphone.phone_number,
                    userphone.phone_token,
                    response
                )
            else:
                logger.info(f"Valid token confirmed for phone: {userphone.phone_number}")
                print(f"✅ Valid token for {userphone.phone_number}")
                
        except Exception as e:
            logger.error(
                f"Error processing phone {userphone.phone_number}",
                exc_info=True,
                extra={'phone': userphone.phone_number}
            )
            print(f"❌ Error processing {userphone.phone_number}: {str(e)}")
            
    return invalid_tokens

    

def main():
    """Main execution function."""
    all_invalid_tokens = []
    total_processed = 0
    
    try:
        print("\n🔍 Checking database connection...")
        queryset = UserPhone.objects.all()
        total_phones = queryset.count()
        
        if total_phones == 0:
            logger.warning("No UserPhone records found in database")
            print("❌ No UserPhone records found in database! Please check if:")
            print("   1. Database is properly connected")
            print("   2. UserPhone table has records")
            print("   3. Django migrations are up to date")
            return
            
        logger.info(f"Starting token validation for {total_phones} phones")
        print(f"\n🚀 Starting token validation for {total_phones} phones...")
        
        for i in range(0, total_phones, BATCH_SIZE):
            batch = list(queryset[i:i + BATCH_SIZE])
            invalid_batch = process_batch(batch)
            all_invalid_tokens.extend(invalid_batch)
            total_processed += len(batch)
            print(f"\n📊 Progress: {total_processed}/{total_phones} phones processed")
            logger.info(f"Processed {total_processed}/{total_phones} phones")
            
        if all_invalid_tokens:
            try:
                send_invalid_token_notification(all_invalid_tokens)
                logger.info(f"Notification sent for {len(all_invalid_tokens)} invalid tokens")
                print(f"\n📧 Notification sent for {len(all_invalid_tokens)} invalid tokens")
            except Exception as e:
                logger.error("Failed to send notification", exc_info=True)
                print(f"\n❌ Failed to send notification: {str(e)}")
                
        logger.info("Token validation completed successfully")
        print("\n✨ Token validation completed successfully")
        
    except Exception as e:
        logger.error("Script execution failed", exc_info=True)
        print(f"\n❌ Script execution failed: {str(e)}")
        raise

# Phones that are failing to retry sending out of them:
failing_phones_to_try = ["11911215641",
"11996704096",
"11957226396",
"13996332337",
"11996736410",
"4391704662",
"11973235790",
"15996972700",
"11912139220",
"19992874531",
"11911217309",
"21999258232",
"11950519566",
"11943743122",
"11975627009"
]

if __name__ == "__main__":
    main()



failing_stores = [
"MOOCA",
"LAPA",
"MOEMA",
"SANTOS",
"SANTO AMARO",
"LONDRINA",
"IPIRANGA",
"SOROCABA",
"OSASCO",
"CAMPINAS",
"ITAIM",
"TIJUCA",
"TATUAPÉ",
"VILA MASCOTE",
"ALPHAVILLE"
]

failing_tokens = [
    "JMSfC9NHqhSK1EJCnjpnRESvXNXNHR1e",
    "bhPky7VluDP5VBkSw481Qyu1MMuWz3rJ",
    "MlRC23n5BeubCGSDqnQHosBlGhbUOJqC",
    "B9MMjBf1Mtw8FtfrJ77sMcl6ALG9lJAi",
    "jKpdWAkph1WDOJc3y11DhPE59sI4P01O",
    "N7dB5IvxRIAjpJjQUFnpzj55OxHOmxgL",
    "QTcUCilgyCk3d8Si8jvXCFyrcmiMqvQg",
    "Gx183Kuc53R82vIVjhq51f8LWHDezkBD",
    "ToToZOpskyroPcJJWEcjRXl5DzFiQUvG",
    "JTNWYuWiTyY3h4QMvFuop15ZF7jnuyAJ",
    "knYOs0rkBFZwx91VGbujLpvkilqnFz8V",
    "29Vpcy55LWLQ79D8KsTOx193rcjzzgxu",
    "UPgy07zshja7oWgCm3fA449TWk5ip9ga",
    "45PsqRpuAbQseiN944sgL4s6I2VGofiR",
    "pCIAlFffCY44IHOZuOxDF6dLhGAGoZeB"
]