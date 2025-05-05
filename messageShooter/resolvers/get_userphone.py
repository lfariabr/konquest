# get userphone based contact_tag
import logging
from core.models.userphone import UserPhone
from messageShooter.utils.nps_token_dic import store_dict_info
from messageShooter.utils.reminder_token_dic import reminder_token_dict
from messageShooter.utils.vip_token_dic import vip_store_dict_info

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

def get_userphone_ncc(contact_tag, store):
    """
    Develop same rationale as get_userphone_nps
    Have a dictionary of store / attendant / token and possibly the check on message logs to see 
    if contact_phone already received message on the past from an existing userphone to do the match.
    """
    pass

def get_userphone_reminder(contact_tag, store):
    """
    Get userphone token based on contact tag and store of appointment
    Returns a tuple of (userphone, token) or (None, None) if not found
    """
    if contact_tag != 'Reminder':
        logger.error(f"Invalid contact tag: {contact_tag}")
        raise ValueError(f"get_userphone_reminder called with invalid tag: {contact_tag}")
        
    if not store:
        logger.error("No store provided for Reminder")
        return None, None
        
    try:
        store_info = reminder_token_dict.get(store)  # Use .get() instead of calling the dict
        if not store_info:
            logger.error(f"Store {store} not found in reminder_token_dict")
            return None, None
        
        token = store_info.get('token')
        phone = store_info.get('numero_telefone')

        if not token or not phone:
            logger.error(f"Token or phone not found for store {store}")
            return None, None

        logger.info(f"Found Reminder token for store {store}")
        return phone, token
        
    except Exception as e:
        logger.error(f"Error getting Reminder userphone for store {store}: {str(e)}")
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
        # # TODO: Test!
        # try:
        #     userphone = UserPhone.objects.get(relationship_tag='NPSUnique').first()
        #     return userphone, userphone.phone_token
        # except UserPhone.DoesNotExist:
        #     logger.error("No UserPhone found with relationship_tag='NPSUnique'")
        #     return None, None
        
    except Exception as e:
        logger.error(f"Error getting NPS userphone for store {store}: {str(e)}")
        return None, None

def get_userphone_vip(contact_tag, store):
    if contact_tag != 'VIP':
        logger.error(f"Invalid contact tag: {contact_tag}")
        raise ValueError(f"get_userphone_vip called with invalid tag: {contact_tag}")
        
    if not store:
        logger.error("No store provided for VIP")
        return None, None
        
    try:
        store_info = vip_store_dict_info.get(store)  # Use .get() instead of calling the dict
        if not store_info:
            logger.error(f"Store {store} not found in vip_store_dict_info")
            return None, None
        
        token = store_info.get('token')
        phone = store_info.get('numero_telefone')

        if not token or not phone:
            logger.error(f"Token or phone not found for store {store}")
            return None, None

        logger.info(f"Found VIP token for store {store}")
        return phone, token
        
    except Exception as e:
        logger.error(f"Error getting VIP userphone for store {store}: {str(e)}")
        return None, None