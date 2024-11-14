from graphene_django.types import DjangoObjectType
from apiCrm.models.lead import Lead

class LeadType(DjangoObjectType):
    class Meta:
        model = Lead
        fields = '__all__'