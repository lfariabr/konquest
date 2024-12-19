# get userphone based contact_tag
from core.models.userphone import UserPhone

def get_userphone(contact_tag):
    """
    Get userphone and token based on contact tag
    Returns a tuple of (userphone, token) or (None, None) if not found
    
    Each tag is associated with a specific phone number and token for sending messages
    This helps in tracking message sources and maintaining proper sender identity
    """
    try:
        if contact_tag == "Preenchimento":
            userphone = UserPhone.objects.filter(relationship_tag="Preenchimento").first()
        elif contact_tag == "Botox":
            userphone = UserPhone.objects.filter(relationship_tag="Botox").first()
        elif contact_tag == 'Reminder':
            userphone = UserPhone.objects.filter(relationship_tag="Reminder").first()
        else:
            userphone = None

        if userphone:
            return userphone, userphone.phone_token
        return None, None

    except Exception as e:
        print(f"Error getting userphone for tag {contact_tag}: {str(e)}")
        return None, None