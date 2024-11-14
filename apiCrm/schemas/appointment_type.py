from graphene_django.types import DjangoObjectType
import graphene
from apiCrm.models.appointment import Appointment

class AppointmentType(DjangoObjectType):
        appointment_date = graphene.DateTime()
        createdby_created_at = graphene.DateTime()
        
        class Meta:
            model = Appointment
            fields = '__all__'