# apiCrm/views.py

from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.views.decorators.cache import never_cache
from apiCrm.models.lead import Lead
from apiCrm.models.appointment import Appointment
from apiCrm.models.billcharge import BillCharge
from .serializers import LeadSerializer, AppointmentSerializer, BillChargeSerializer

@api_view(['GET'])
@never_cache
def leads_view(request):
    leads = Lead.objects.all()  # Obtém todos os leads do banco de dados
    serializer = LeadSerializer(leads, many=True)  # Serializa a lista de leads
    return Response(serializer.data)  # Retorna a lista de leads como JSON

@api_view(['GET'])
@never_cache
def appointments_view(request):
    appointments = Appointment.objects.all()
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@never_cache
def bill_charges_view(request):
    bill_charges = BillCharge.objects.all()  
    serializer = BillChargeSerializer(bill_charges, many=True)
    return Response(serializer.data)

# Add leads_handler_view
# Add whatsapp_contacts_view 
#   to serve streamlit data area or/spreadsheet
#   to serve hunter algo to recommend procedures
#   to serve future area on Konquist to retrieve chat with whatsapp contacts
#   to serve future algorithm to read messages and classify them
# Add lead score view to serve CRM's graphQL
# Add message logs view to serve CRM's graphQL 