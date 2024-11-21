# if contact_type = whatsapp, counter = Count sent messages to number to specific tag
# if contact_type = appointment, counter = DaysToAppoitment (positive or negative in case of NPS)

from resolvers.get_contacts import get_contact_whatsapp, get_contact_appointment
from core.models.messagelog import MessageLogs

def get_counter_whatsapp(contact_type, contact_tag=None):
    if contact_type == "Whatsapp" and contact_tag == "Preenchimento":
        messages = MessageLogs.objects.filter(message__relationship_tag="Preenchimento").count()
    if contact_type == "Whatsapp" and contact_tag == "Botox":
        messages = MessageLogs.objects.filter(message__relationship_tag="Botox").count()
    return messages

def get_counter_appointment(contact_type, contact_tag=None):
    if contact_type == "Appointment" and contact_tag == "Reschedule":
        messages = MessageLogs.objects.filter(message__relationship_tag="Reschedule").count()
    return messages