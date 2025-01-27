# apiSocialHub/resolvers/monitor.py
"""
This is the monitoring module for apiSocialHub.
It provides functions to monitor the status of text and file messages.
"""
from messageShooter.services.email_alert import send_nps_failure_notification, end_of_queue_email
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

stores_with_invalid_token = []
api_token_expected_response = {"success": False, "message": "invalid api_token!"}

def queue_finished():
    """
    Send an email saying that the monitoring service has finished running after Queue completion
    """
    end_of_queue_email()


def send_invalid_tokens_notification():
    """
    Send a consolidated email notification for all stores with invalid tokens.
    After sending the notification, clear the stores list.
    
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    if not stores_with_invalid_token:
        logger.info("No invalid tokens to report")
        return False
        
    try:
        # Format the message with all invalid token stores
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"""
        Os tokens abaixo estão inválidos no disparo de hoje, ({current_time}):
        """
        # Group by token to show which token is invalid for which stores
        token_groups = {}
        for store in stores_with_invalid_token:
            token = store['token']
            if token not in token_groups:
                token_groups[token] = []
            token_groups[token].append(store['phone'])
            
        # Add each group to the message
        for token, phones in token_groups.items():
            message += f"\nToken: {token}\n"
                        
        # Send the notification
        send_nps_failure_notification(message)
        
        # Clear the list after sending
        stores_with_invalid_token.clear()
        logger.info("Invalid tokens notification sent and store list cleared")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send invalid tokens notification: {e}")
        return False

def monitor_api_response(phone, token_socialhub, response_json):
    """Monitor API responses for invalid tokens and store them for later notification.
    
    Args:
        phone (str): The phone number being processed
        token_socialhub (str): The API token being used
        response_json (str): The JSON response from the API as a string
    """
    try:
        # Parse the JSON string to a dictionary
        if isinstance(response_json, str):
            response_data = json.loads(response_json)
        else:
            response_data = response_json
            
        logger.info(f"Monitoring response for phone {phone}: {response_data}")
        
        if response_data == api_token_expected_response:
            store_info = {"phone": phone, "token": token_socialhub}
            if store_info not in stores_with_invalid_token:
                stores_with_invalid_token.append(store_info)
                logger.info(f"Stores with invalid token: {stores_with_invalid_token}")
                
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse response JSON for phone {phone}: {e}")
    except Exception as e:
        logger.error(f"Error monitoring response for phone {phone}: {e}")

def send_monitor_email():
    """Send an email with the stores with invalid tokens."""
    pass