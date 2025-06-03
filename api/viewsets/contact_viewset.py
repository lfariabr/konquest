from rest_framework import viewsets
from core.models.contact import Contact
from api.serializers.contact_serializer import ContactSerializer

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
