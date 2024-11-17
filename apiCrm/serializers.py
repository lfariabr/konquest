from rest_framework import serializers
from apiCrm.models.lead import Lead
from apiCrm.models.appointment import Appointment
from apiCrm.models.billcharge import BillCharge

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    customer_id = serializers.CharField(allow_blank=True)

    class Meta:
        model = Appointment
        fields = '__all__'

class BillChargeSerializer(serializers.ModelSerializer):
    customer_id = serializers.CharField(allow_blank=True)

    class Meta:
        model = BillCharge
        fields = '__all__'