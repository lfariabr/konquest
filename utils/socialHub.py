from apiSocialHub.resolvers.send_text_message import send_text_message
from logging import getLogger

logger = getLogger(__name__)

DEBUG_NOTIFY = {
    'enabled': True,
    'phone': '11963546222',  # Your phone number
    'token': 'rmvYoOnWD5WjcH7Bx5lYTZkGMX2vweN1'  # Your token
}

def send_debug_notification(message):
    """Simple helper to send debug notifications to WhatsApp"""
    if DEBUG_NOTIFY['enabled']:
        try:
            send_text_message(
                DEBUG_NOTIFY['phone'], 
                message,
                DEBUG_NOTIFY['token'],
                None
            )
        except Exception as e:
            logger.error(f"Failed to send debug WhatsApp message: {str(e)}")