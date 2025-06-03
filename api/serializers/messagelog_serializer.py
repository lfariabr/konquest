from rest_framework import serializers
from core.models.messagelog import MessageLogs

class MessageLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageLogs
        fields = '__all__'