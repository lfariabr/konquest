from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from core.models.messagelog import MessageLogs
from api.serializers.messagelog_serializer import MessageLogsSerializer

class MessageLogsViewSet(viewsets.ModelViewSet):
    serializer_class = MessageLogsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['relationship_tag'] # api/messagelogs/?relationship_tag=Botox

    def get_queryset(self):
        return MessageLogs.objects.filter(user_id=self.request.user.id).order_by('-sent_at')