"""
Script to send debug notifications to VIPs dict:
python scripts/x9_vip.py
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
from messageShooter.utils.vip_token_dic import vip_store_dict_info
from konquist.settings import ADMIN_PHONE

"""
This script validates VIP store tokens by attempting to send test messages.
It processes tokens from vip_token_dic.py, monitors for invalid tokens,
and notifies the team about any issues found.
"""

# Configure logging
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

TEST_MESSAGE = "VIP Token Validation Test"

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

def process_vip_tokens() -> List[Tuple[str, str, str]]:
    """
    Process VIP store tokens and return invalid ones.
    
    Returns:
        List of tuples containing (store_name, phone_number, token) for invalid tokens
    """
    invalid_tokens = []
    total_stores = len(vip_store_dict_info)
    processed = 0
    
    for store_name, store_info in vip_store_dict_info.items():
        try:
            token = store_info['token']
            phone = store_info['numero_telefone']
            
            logger.info(f"Testing token for VIP store: {store_name}")
            print(f"🔍 Testing token for {store_name} (Phone: {phone})...")
            
            response = send_text_message(
                ADMIN_PHONE,
                TEST_MESSAGE,
                token,
                'vip_validation'
            )
            
            if not validate_api_response(response):
                logger.warning(
                    f"Invalid token detected for store: {store_name}",
                    extra={
                        'store': store_name,
                        'phone': phone,
                        'token': token,
                        'response': response
                    }
                )
                print(f"❌ Invalid token found for {store_name}")
                invalid_tokens.append((store_name, phone, token))
                monitor_api_response(phone, token, response)
            else:
                logger.info(f"Valid token confirmed for store: {store_name}")
                print(f"✅ Valid token for {store_name}")
                
        except Exception as e:
            logger.error(
                f"Error processing store {store_name}",
                exc_info=True,
                extra={'store': store_name, 'phone': phone}
            )
            print(f"❌ Error processing {store_name}: {str(e)}")
            
        processed += 1
        print(f"\n📊 Progress: {processed}/{total_stores} stores processed")
            
    return invalid_tokens

def main():
    """Main execution function."""
    try:
        print("\n🔍 Starting VIP token validation...")
        logger.info("Starting VIP token validation")
        
        if not vip_store_dict_info:
            logger.warning("No VIP stores found in dictionary")
            print("❌ No VIP stores found! Please check vip_token_dic.py")
            return
            
        invalid_tokens = process_vip_tokens()
        
        if invalid_tokens:
            # Format the message with store name, phone, token and conta_social_hub
            message_lines = []
            for store, phone, token in invalid_tokens:
                conta_social = vip_store_dict_info[store]["conta_social_hub"]
                message_lines.append(f"Store: {store}")
                message_lines.append(f"Conta Social: {conta_social}")
                message_lines.append(f"Phone: {phone}")
                message_lines.append(f"Token: {token}")
                message_lines.append("---")
            
            notification_message = "\n".join(message_lines)
            try:
                send_invalid_token_notification(notification_message)
                logger.info(f"Notification sent for {len(invalid_tokens)} invalid tokens")
                print(f"\n📧 Notification sent for {len(invalid_tokens)} invalid tokens")
                
                # Print detailed report
                print("\n📋 Invalid Token Report:")
                for store, phone, token in invalid_tokens:
                    conta_social = vip_store_dict_info[store]["conta_social_hub"]
                    print(f"   Store: {store}")
                    print(f"   Conta Social: {conta_social}")
                    print(f"   Phone: {phone}")
                    print(f"   Token: {token}")
                    print("   ---")
            except Exception as e:
                logger.error("Failed to send notification", exc_info=True)
                print(f"\n❌ Failed to send notification: {str(e)}")
                
        logger.info("VIP token validation completed successfully")
        print("\n✨ VIP token validation completed successfully")
        
    except Exception as e:
        logger.error("Script execution failed", exc_info=True)
        print(f"\n❌ Script execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
