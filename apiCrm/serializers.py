from rest_framework import serializers
from .models import Lead, Appointment, BillCharge

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

class BillChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillCharge
        fields = '__all__'