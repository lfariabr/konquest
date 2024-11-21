# if contact_type = whatsapp > get Contacts order FIFO
# if contact_type = whatsapp + contact_tag[Botox] > get Contact Botox order FIFO

# if contact_type > get Appointment
3 # if contact_type = Appointment + contact_tag[Reschedule] > get Appointment Reschedule

from core.models.contact import Contact
from core.models.appointment import Appointment

def get_contact_whatsapp(contact_type, contact_tag=None):
    if contact_type == "Whatsapp" and contact_tag == "Botox":
        contacts = Contact.objects.filter(source="Whatsapp", tag="Botox").order_by('created_at')
    if contact_type == "Whatsapp" and contact_tag == "Preenchimento":
        contacts = Contact.objects.filter(source="Whatsapp", tag="Preenchimento").order_by('created_at')

def get_contact_appointment(contact_type, contact_tag=None):
    if contact_type == "Appointment" and contact_tag == "Reschedule": 
        contacts = Appointment.objects.filter(status="Reschedule").order_by('created_at')
        # How to filter "check_if_appointment_is_evaluation" to optimize this part ?
