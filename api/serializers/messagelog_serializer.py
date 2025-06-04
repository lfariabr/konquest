from rest_framework import serializers
from core.models.messagelog import MessageLogs

class MessageLogsSerializer(serializers.ModelSerializer):
   """
   Serializer for the MessageLogs model.
   Handles serialization and deserialization of MessageLogs instances.
   """
   
   id = serializers.ReadOnlyField()
   created_at = serializers.DateTimeField(read_only=True)
   
   class Meta:
      model = MessageLogs
      fields = '__all__'
      read_only_fields = ['id', 'created_at']