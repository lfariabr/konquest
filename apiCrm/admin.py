from django.contrib import admin
from .models.lead import Lead
from .models.appointment import Appointment
from .models.billcharge import BillCharge


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

class BillChargeAdmin(admin.ModelAdmin):
    # Update list_display to reflect actual fields in the BillCharge model
    list_display = [
        'quote_id',         # Update with valid field names
        'customer_name',
        'store_name',
        'total_amount',
        'quote_items',
        'status',
        'is_paid',
        'paid_at',          # Ensure these fields exist in the model
        'due_at'
    ]

    # Set ordering by fields that exist in BillCharge model
    ordering = ['paid_at']  # Replace 'bill_date' with an actual field, like 'paid_at'

    # Define list filters with existing fields in BillCharge model
    list_filter = ['is_paid', 'store_name', 'status']

admin.site.register(BillCharge, BillChargeAdmin)

# AppointmentsAdmin - ok
# BillChargesAdmin - ok

# LeadsHandlerAdmin
# SentMessagesAdmin
# ContactsAdmin
# MessagesAdmin
# UserPhonesAdmin
# UsersAdmin
# Permissions Admin (admin / viewer)
# Streamlit within admin panel showing cool graphs
