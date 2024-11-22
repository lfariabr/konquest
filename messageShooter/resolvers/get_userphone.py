# get userphone based contact_tag
from core.models.userphone import UserPhone

def get_userphone(contact_tag):
    if contact_tag == "Preenchimento":
        userphone = UserPhone.objects.filter(relationship_tag="Preenchimento").first()
    if contact_tag == "Botox":
        userphone = UserPhone.objects.filter(relationship_tag="Botox").first()
    if contact_tag == "NPS":
        userphone = UserPhone.objects.filter(relationship_tag="NPS").first()
    if contact_tag == "Google My Business":
        userphone = UserPhone.objects.filter(relationship_tag="Google My Business").first()
    else:
        userphone = None
    return userphone