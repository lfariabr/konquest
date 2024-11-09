# apiCrm/views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Lead
from .serializers import LeadSerializer

@api_view(['GET'])
def leads_view(request):
    leads = Lead.objects.all()  # Obtém todos os leads do banco de dados
    serializer = LeadSerializer(leads, many=True)  # Serializa a lista de leads
    return Response(serializer.data)  # Retorna a lista de leads como JSON

# Add appointments_view
# Add leads_handler_view (not now)
# Add whatsapp_contacts_view 
#   to serve streamlit data area or/spreadsheet
#   to serve hunter algo to recommend procedures
#   to serve future area on Konquist to retrieve chat with whatsapp contacts
#   to serve future algorithm to read messages and classify them
# Add lead score view to serve CRM's graphQL
# Add message logs view to serve CRM's graphQL 