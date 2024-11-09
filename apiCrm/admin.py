from django.contrib import admin
from .models import Lead, Appointment
# from .serializers import LeadSerializer

class LeadAdmin(admin.ModelAdmin):
    list_display = ['id_crm', 'name', 'email', 'phone', 'source', 'store', 'status', 'customer_id', 'created_at']
    search_fields = ['name', 'email', 'phone']
    list_filter = ['source', 'store', 'status']
    ordering = ['-created_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # You can filter the queryset here if needed
        return queryset

admin.site.register(Lead, LeadAdmin)

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id_crm', 'appointment_date', 'store_name', 'customer_name', 'status_label', 'procedure_name', 'employee_name', 'createdby_name', 'createdby_created_at']
    search_fields = ['appointment_date', 'store_name', 'customer_name', 'status_label', 'procedure_name']
    list_filter = ['appointment_date', 'store_name']
    ordering = ['-appointment_date']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # You can filter the queryset here if needed
        return queryset

admin.site.register(Appointment, AppointmentAdmin)

# AppointmentsAdmin - ok

# LeadsHandlerAdmin
# SentMessagesAdmin
# ContactsAdmin
# MessagesAdmin
# UserPhonesAdmin
# UsersAdmin
# Permissions Admin (admin / viewer)
# Streamlit within admin panel showing cool graphs
