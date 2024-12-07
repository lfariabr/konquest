from .serializers import LeadSerializer
from apiCrm.schemas.lead_type import LeadType

def process_and_save_leads(leads_data):
    leads_list = []
    for raw_lead in leads_data:
        formatted_lead = format_lead_data(raw_lead)
        serializer = LeadSerializer(data=formatted_lead)
        if serializer.is_valid():
            serializer.save()
            leads_list.append(LeadType(**serializer.validated_data))
        else:
            print(f"Failed to save lead: {serializer.errors}")
    return leads_list