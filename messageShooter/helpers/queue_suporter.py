from messageShooter.services.get_message_for_contact import get_message_for_contact
from messageShooter.resolvers.get_userphone import get_userphone, get_userphone_nps, get_userphone_reminder, get_userphone_vip
from core.models.userphone import UserPhone
from logging import getLogger
from asgiref.sync import sync_to_async

logger = getLogger(__name__)

async def get_message_for_contact_async(contact, target_list):
    return await sync_to_async(get_message_for_contact)(contact, target_list)

async def get_userphone_async(contact, target_list):
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