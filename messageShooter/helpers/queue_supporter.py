from messageShooter.services.get_message_for_contact import get_message_for_contact
from messageShooter.resolvers.get_userphone import get_userphone, get_userphone_nps, get_userphone_reminder, get_userphone_vip
from core.models.userphone import UserPhone
from logging import getLogger
from asgiref.sync import sync_to_async

logger = getLogger(__name__)

# Enhanced logging for debugging async wrapper and refactor issues
async def get_message_for_contact_async(contact, target_list):
    """
    Get message for contact
    """

    logger.info(f"[queue_suporter] Calling get_message_for_contact for contact={getattr(contact, 'id', contact)} target_list={getattr(target_list, 'id', target_list)}")
    
    try:
        result = await sync_to_async(get_message_for_contact)(contact, target_list)
        logger.info(f"[queue_suporter] get_message_for_contact returned: {result}")
        if not isinstance(result, tuple) or len(result) != 2:
            logger.error(f"[queue_suporter] get_message_for_contact returned unexpected result: {result}")
        return result
    
    except Exception as e:
        logger.error(f"[queue_suporter] Error in get_message_for_contact_async: {e}", exc_info=True)
        raise

async def get_userphone_async(contact, target_list):
    """
    Get user phone and token for contact
    """

    def get_userphone_wrapper():
        tag = target_list.contact_tag
        store = getattr(contact, "store", None)
        if tag == 'NPS':
            phone, token = get_userphone_nps(tag, store)
            if phone and token:
                try:
                    userphone = UserPhone.objects.get(phone_number=phone, relationship_tag=tag)
                    logger.info(f"Found existing UserPhone for NPS store {store}")
                    return userphone, token
                except UserPhone.DoesNotExist:
                    userphone = UserPhone.objects.create(
                        phone_number=phone,
                        phone_token=token,
                        relationship_tag=tag,
                        user=contact.user
                    )
                    logger.info(f"Created new UserPhone for NPS store {store}")
                    return userphone, token

        elif tag == 'Reminder':
            phone, token = get_userphone_reminder(tag, store)
            if phone and token:
                try:
                    userphone = UserPhone.objects.get(phone_number=phone, relationship_tag=tag)
                    logger.info(f"Found existing UserPhone for Reminder store {store}")
                    return userphone, token
                except UserPhone.DoesNotExist:
                    userphone = UserPhone.objects.create(
                        phone_number=phone,
                        phone_token=token,
                        relationship_tag=tag,
                        user=contact.user,
                        phone_description=store
                    )
                    logger.info(f"Created new UserPhone for Reminder store {store}")
                    return userphone, token

        elif tag == 'VIP':
            phone, token = get_userphone_vip(tag, store)
            if phone and token:
                try:
                    userphone = UserPhone.objects.get(phone_number=phone, relationship_tag=tag)
                    logger.info(f"Found existing UserPhone for VIP store {store}")
                    return userphone, token
                except UserPhone.DoesNotExist:
                    userphone = UserPhone.objects.create(
                        phone_number=phone,
                        phone_token=token,
                        relationship_tag=tag,
                        user=contact.user,
                        phone_description=store
                    )
                    logger.info(f"Created new UserPhone for VIP store {store}")
                    return userphone, token

        else:
            userphone, token = get_userphone(tag)
            return userphone, token
        return None, None

    return await sync_to_async(get_userphone_wrapper)()


def get_status_msg(queue_item, success_count, total_contacts, final_status, error_count):
    """
    Get status message for queue item
    """

    if final_status == 'sent' and success_count == total_contacts:
        return f"✨ Queue {queue_item.id}: Completed successfully! {success_count}/{total_contacts} messages sent"

    elif final_status == 'sent' and error_count > 0:
        return f"⚠️ Queue {queue_item.id}: Partially completed. {success_count}/{total_contacts} sent, {error_count}/{total_contacts} failed"

    else:
        return f"💥 Queue {queue_item.id}: Failed completely. {error_count}/{total_contacts} messages failed"

LEAD_MESSAGES = [
            "Lead da campanha Botox",
            "Lead da campanha Preenchimento",
            "Lead da bio do Instagram"
        ]