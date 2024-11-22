# priority 

# contact phone
# contact_type
# contact_tag
# reference_id = {
#   (if whatsapp, core>models>contact>id),
#   (if appointment, apiCrm>models>appointment>id_crm)
#   (if lead, apiCrm>models>lead),
#}

# sent_messages_count

# userphone token

from django.db import models
from core.models.userphone import UserPhone
from core.models.user import kUser
from core.models.contact import Contact
from apiCrm.models.lead import Lead
from apiCrm.models.appointment import Appointment

class TargetList(models.Model):
    # from resolvers.get_contacts
    contact_phone = models.CharField(max_length=20)
    contact_type = models.CharField(max_length=100)
    contact_tag = models.CharField(max_length=100)
    reference_id = models.CharField(max_length=100)

    # from resolvers.get_counter
    sent_messages_count = models.IntegerField(default=0)
    # from resolvers.getuserphone
    userphone = models.ForeignKey(UserPhone, on_delete=models.CASCADE)
    #from resolvers.get_message
    message = models.ForeignKey(Message, on_delete=models.CASCADE)

    # from models.job
    # priority
    # status
