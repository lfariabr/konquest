import graphene
from apiCrm.schemas.lead_type import LeadType
from apiCrm.schemas.appointment_type import AppointmentType
from apiCrm.schemas.bill_charges_type import BillChargeType

class AllDataType(graphene.ObjectType):
    leads = graphene.List(LeadType)
    appointments = graphene.List(AppointmentType)
    bill_charges = graphene.List(BillChargeType)