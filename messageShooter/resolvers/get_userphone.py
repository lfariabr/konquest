# get userphone based contact_tag
from core.models.userphone import UserPhone
from messageShooter.utils.nps_token_dic import store_dict_info
import logging

logger = logging.getLogger(__name__)

def get_userphone(contact_tag):
    """
    Get userphone and token based on contact tag
    Returns a tuple of (userphone, token) or (None, None) if not found
    """
    try:
        # Always get the oldest phone for consistency
        userphone = UserPhone.objects.filter(relationship_tag=contact_tag).order_by('created_at').first()
        return (userphone, userphone.phone_token) if userphone else (None, None)

    except Exception as e:
        print(f"Error getting userphone for tag {contact_tag}: {str(e)}")
        return None, None

def get_userphone_nps(contact_tag, store):
    """
    Get userphone token based on contact tag and store of appointment
    Returns a tuple of (userphone, token) or (None, None) if not found
    """
    if contact_tag != 'NPS':
        raise ValueError(f"get_userphone_nps called with invalid tag: {contact_tag}")
        
    if not store:
        logger.error("No store provided for NPS")
        return None, None
        
    try:
        store_info = store_dict_info.get(store)  # Use .get() instead of calling the dict
        if not store_info:
            logger.error(f"Store {store} not found in store_dict_info")
            return None, None
        
        token = store_info.get('token')
        phone = store_info.get('numero_telefone')

        if not token or not phone:
            logger.error(f"Token or phone not found for store {store}")
            return None, None

        logger.info(f"Found NPS token for store {store}")
        return phone, token
        
    except Exception as e:
        logger.error(f"Error getting NPS userphone for store {store}: {str(e)}")
        return None, None