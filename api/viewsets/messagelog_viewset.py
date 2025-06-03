from rest_framework import viewsets
from core.models.messagelog import MessageLogs
from api.serializers.messagelog_serializer import MessageLogsSerializer

class MessageLogsViewSet(viewsets.ModelViewSet):
    queryset = MessageLogs.objects.all()
    serializer_class = MessageLogsSerializer
    