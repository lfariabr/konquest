# get userphone based contact_tag
from core.models.userphone import UserPhone

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