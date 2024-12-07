from .serializers import AppointmentSerializer
from apiCrm.schemas.appointment_type import AppointmentType

def process_and_save_appointments(appointments_data):
    appointments_list = []
    for raw_appointment in appointments_data:
        formatted_appointment = format_appointment_data(raw_appointment)
        serializer = AppointmentSerializer(data=formatted_appointment)
        if serializer.is_valid():
            serializer.save()
            appointments_list.append(AppointmentType(**serializer.validated_data))
        else:
            print(f"Failed to save appointment: {serializer.errors}")
    return appointments_list