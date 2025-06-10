from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from core.models.contact import Contact
from api.serializers.contact_serializer import ContactSerializer

class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['relationship_tag']  # api/contacts/?relationship_tag=Botox

    def get_queryset(self):
        return Contact.objects.filter(user_id=self.request.user.id).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context
