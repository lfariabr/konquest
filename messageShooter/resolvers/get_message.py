# according to contact type, counter, contact tag, 
# grab message from core>message

from core.models.message import Message
from resolvers.get_contacts import get_contact_whatsapp, get_contact_appointment
from resolvers.get_counter import get_counter_whatsapp, get_counter_appointment

def get_message(contact_type, contact_tag=None, counter=None):
    if contact_type == "Whatsapp":
        contact = get_contact_whatsapp(contact_type, contact_tag)
        counter = get_counter_whatsapp(contact_type, contact_tag)
    if contact_type == "Appointment":
        contact = get_contact_appointment(contact_type, contact_tag)
        counter = get_counter_appointment(contact_type, contact_tag)
    message = Message.objects.get(counter=counter)
    return message

    #TODO # I don think this is correct... stopping here...