from rest_framework import serializers
from core.models.contact import Contact
from core.models.user import kUser
from django.utils import timezone

class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for the Contact model.
    Handles serialization and deserialization of Contact instances.
    """
    # Read-only fields that shouldn't be modified directly
    id = serializers.ReadOnlyField()
    created_at = serializers.DateTimeField(read_only=True)
    
    # User field - only show user ID in responses, but allow setting by ID on create/update
    user = serializers.PrimaryKeyRelatedField(
        queryset=kUser.objects.all(),
        required=True,
        help_text="ID of the user who owns this contact"
    )
    
    class Meta:
        model = Contact
        fields = [
            # Core fields
            'id', 'name', 'phone', 'created_at', 'relationship_tag',
            'source', 'store', 'user',
            'available_to_queue', 'priority',
        ]
        read_only_fields = [
            'id', 'created_at',
        ]

    def validate_phone(self, value):
        """
        Validate phone number format.
        Removes any non-digit characters and ensures minimum length.
        """
        if not value:
            raise serializers.ValidationError("Phone number is required")
            
        # Remove all non-digit characters
        cleaned = ''.join(filter(str.isdigit, str(value)))
        
        # Basic validation - adjust according to your needs
        if len(cleaned) < 10:
            raise serializers.ValidationError("Phone number is too short")
            
        return cleaned
    
    def validate_priority(self, value):
        """Ensure priority is between 1 and 5."""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Priority must be between 1 and 5")
        return value
    
    def create(self, validated_data):
        """Create and return a new Contact instance."""
        return Contact.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update and return an existing Contact instance."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance