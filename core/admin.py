import csv
import logging
import tempfile
import os
from django.contrib import admin, messages
from core.models.user import kUser
from core.models.contact import Contact
from core.models.userphone import UserPhone
from core.models.message import Message
from core.models.messagelog import MessageLogs
from core.forms.contact_upload import ContactCsvUploadForm
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from datetime import datetime
from django.utils import timezone
from core.resolvers.clean_phone_number import clean_phone_number
from core.resolvers.process_csv_files import process_csv_files

class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company')
    search_fields = ('name', 'email', 'company')
    list_filter = ('company',)
    ordering = ['-created_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

admin.site.register(kUser, UserAdmin)

class UserPhoneAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'user', 'phone_token', 'phone_description', 'relationship_tag', 'created_at')
    search_fields = ('phone_number', 'user__name', 'relationship_tag')
    list_filter = ('user', 'phone_description', 'relationship_tag')
    ordering = ['-created_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

admin.site.register(UserPhone, UserPhoneAdmin)

class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'text', 'counter' ,'file_type', 'relationship_tag', 'created_at')
    search_fields = ('user__name', 'title', 'text', 'relationship_tag')
    list_filter = ('user', 'title', 'relationship_tag', 'created_at')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

admin.site.register(Message, MessageAdmin)

class MessageLogsAdmin(admin.ModelAdmin):
    list_display = ('get_message_text', 'status', 'sent_at', 'get_contact_phone_number', 'relationship_tag', 'get_phone_number')
    search_fields = ('message__title', 'user__name', 'user_phone__phone_number', 'contact__name', 'relationship_tag')
    list_filter = ('sent_at', 'user_phone', 'contact', 'relationship_tag')
    ordering = ['-sent_at']
    list_per_page = 20

    def get_contact_phone_number(self, obj): 
        return obj.contact.phone if obj.contact else '-'
    get_contact_phone_number.short_description = 'Contact Phone'

    def get_message_text(self, obj):
        return obj.message.text
    get_message_text.short_description = 'Message'

    def get_phone_number(self, obj):
        # return obj.phone_number
        return obj.user_phone.phone_number if obj.user_phone else '-'

    get_phone_number.short_description = 'Phone Number'

    # def get_queryset(self, request):
    #     queryset = super().get_queryset(request)
    #     return queryset
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('message', 'user', 'user_phone', 'contact')

admin.site.register(MessageLogs, MessageLogsAdmin)

class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'relationship_tag', 'created_at', 'source',
                    'store', 'region', 'external_tag', 'status', 
                    'is_lead', 'lead_id', 'lead_status', 'lead_created_at', 'lead_last_checked', 'lead_check_count', 'store_lead',
                    'is_appointment', 'appointment_id', 'appointment_status', 'appointment_created_at', 'appointment_last_checked', 'appointment_check_count', 'store_appointment')
    list_filter = ('source', 'store', 'relationship_tag')
    search_fields = ['phone']
    change_list_template = "admin/contacts_changelist.html"
    actions = ['check_leads', 'check_appointments'] # send_text_message_action, send_file_message_action
    ordering = ['-created_at']
    list_per_page = 20 # change this

    def check_leads(self, request, queryset):
        total = queryset.count()
        found = 0
        for contact in queryset:
            lead = contact.check_if_lead_exists()
            if lead:
                found += 1
        
        self.message_user(
            request,
            f"Checked {total} contacts. Found {found} leads.",
            messages.SUCCESS
        )
    check_leads.short_description = "Check selected contacts for leads"

    def check_appointments(self, request, queryset):
        total = queryset.count()
        found = 0
        for contact in queryset:
            appointment = contact.check_if_appointment_exists()
            if appointment:
                found += 1
        
        self.message_user(
            request,
            f"Checked {total} contacts. Found {found} appointments.",
            messages.SUCCESS
        )
    check_appointments.short_description = "Check selected contacts for appointments"

    def changelist_view(self, request, extra_context=None):
        logging.info("Entered CSV Upload Admin")

        if request.method == 'POST' and 'csv_upload' in request.POST:
            # Handle optional date field
            date_str = request.POST.get('date', '').strip()
            created_date = timezone.now()  # Default to current time
            if date_str:
                try:
                    # Convert the date string to datetime at midnight
                    date_only = datetime.strptime(date_str, '%Y-%m-%d')
                    created_date = timezone.make_aware(date_only)
                except ValueError:
                    self.message_user(request, "Invalid date format. Please use YYYY-MM-DD.", level=messages.ERROR)
                    return HttpResponseRedirect(reverse('admin:core_contact_changelist'))

            # Handle uploaded files
            botox_file = request.FILES.get('botox_file')
            preenchimento_file = request.FILES.get('preenchimento_file')

            if not botox_file and not preenchimento_file:
                self.message_user(request, "No files selected.", level=messages.ERROR)
                return HttpResponseRedirect(reverse('admin:core_contact_changelist'))

            # Process files
            for csv_file in [botox_file, preenchimento_file]:
                if csv_file:
                    self._process_csv_file(csv_file, created_date, request)

            self.message_user(request, "Contacts uploaded successfully.", level=messages.SUCCESS)
            return HttpResponseRedirect(reverse('admin:core_contact_changelist'))

        # Pass extra context for the upload form
        extra_context = extra_context or {}
        extra_context['form'] = ContactCsvUploadForm()
        return super().changelist_view(request, extra_context=extra_context)

    def _process_csv_file(self, csv_file, created_date, request):
        try:
            # Create temporary file to store the CSV data
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv') as temp_file:
                temp_file.write(csv_file.read().decode('utf-8'))
                temp_path = temp_file.name

            try:
                # Process CSV using process_csv_files
                is_preenchimento = 'preenchimento' in csv_file.name.lower()
                if is_preenchimento:
                    df_leads = process_csv_files(preenchimento_file_path=temp_path)
                else:
                    df_leads = process_csv_files(botox_file_path=temp_path)

                # Get or create kUser
                try:
                    k_user = kUser.objects.get(email=request.user.email)
                except kUser.DoesNotExist:
                    k_user = kUser.objects.create(
                        name=request.user.get_full_name() or request.user.username,
                        email=request.user.email,
                        password=request.user.password
                    )

                # Create contacts from processed DataFrame
                row_count = 0
                for _, row in df_leads.iterrows():
                    try:
                        Contact.objects.create(
                            name=row['Nome'],
                            phone=clean_phone_number(row['Whatsapp']),
                            created_at=created_date,
                            store=row['Unidade'],
                            region=row['Região'],
                            external_tag=row['Tags'],
                            relationship_tag='Preenchimento' if is_preenchimento else 'Botox',
                            source='Whatsapp',
                            user=k_user
                        )
                        row_count += 1
                    except Exception as e:
                        logging.error(f"Error processing row: {row}, Error: {e}")
                        continue
                print(f"Successfully processed {row_count} rows from file {csv_file.name}.")
                logging.info(f"Successfully processed {row_count} rows from file {csv_file.name}.")

            finally:
                # Clean up temporary file
                os.unlink(temp_path)

        except Exception as e:
            logging.error(f"Error processing file {csv_file.name}: {e}")
            self.message_user(request, f"Error processing file {csv_file.name}: {e}", level=messages.ERROR)

admin.site.register(Contact, ContactAdmin)