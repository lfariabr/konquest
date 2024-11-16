import csv
import logging
from django.contrib import admin, messages
from core.models.user import User
from core.models.contact import Contact
from core.models.userphone import UserPhone
from core.models.message import Message
from core.models.messagelog import MessageLogs
from core.forms.contact_upload import ContactCsvUploadForm
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from datetime import datetime

class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company')
    search_fields = ('name', 'email', 'company')
    list_filter = ('company',)
    ordering = ['-created_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

admin.site.register(User, UserAdmin)

class UserPhoneAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'user', 'phone_token', 'phone_description')
    search_fields = ('phone_number', 'user__name')
    list_filter = ('user', 'phone_description')
    ordering = ['-created_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

admin.site.register(UserPhone, UserPhoneAdmin)

class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'text', 'file_type')
    search_fields = ('user__name', 'title', 'text')
    list_filter = ('user', 'title', 'text')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

admin.site.register(Message, MessageAdmin)

class MessageLogsAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'user_phone', 'contact', 'sent_at')
    search_fields = ('message__title', 'user__name', 'user_phone__phone_number', 'contact__name')
    list_filter = ('sent_at', 'user', 'user_phone', 'contact')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

admin.site.register(MessageLogs, MessageLogsAdmin)

class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'user', 'created_at', 'source', 'store', 'region', 'external_tag', 'relationship_tag')
    change_list_template = "admin/contacts_changelist.html"
    # paginator #TODO add paginator

    def changelist_view(self, request, extra_context=None):
        logging.info("Entered CSV Upload Admin")

        if request.method == 'POST' and 'csv_upload' in request.POST:
            # Handle optional date field
            date_str = request.POST.get('date', '')
            if not date_str:
                created_date = datetime.now()
            else:
                try:
                    created_date = datetime.strptime(date_str, '%Y-%m-%d')
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
            # Decode and read the CSV file
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            row_count = 0  # Counter for processed rows
            for row in reader:
                try:
                    # Extract data from CSV
                    name = row.get('Nome')
                    phone = row.get('Whatsapp')
                    store = row.get('Unidade', 'CENTRAL')
                    region = row.get('Região', 'São Paulo')
                    external_tag = row.get('Tags', 'SEM TAGS')
                    tag = 'Preenchimento' if csv_file.name and 'preenchimento' in csv_file.name.lower() else 'Botox'

                    # Validate data
                    if not name or not phone:
                        logging.warning(f"Skipping row with missing data: {row}")
                        continue
                    
                    actual_user = request.user
                    # actual_user = request.user._wrapped if hasattr(request.user, '_wrapped') else request.user
                    logging.info(f"Type of actual_user: {type(actual_user)}")
                    logging.info(f"User instance: {actual_user}")
                    # Save to database
                    Contact.objects.create(
                        name=name,
                        phone=phone,
                        created_at=created_date,
                        store=store,
                        region=region,
                        external_tag=external_tag,
                        relationship_tag=tag,
                        source='Whatsapp',
                        user=actual_user
                    )
                    logging.info(f"Processed row: {row}")
                    row_count += 1

                except Exception as e:
                    logging.error(f"Error processing row: {row}, Error: {e}")
                    continue

            logging.info(f"Successfully processed {row_count} rows from file {csv_file.name}.")

        except Exception as e:
            logging.error(f"Error processing file {csv_file.name}: {e}")
            self.message_user(request, f"Error processing file {csv_file.name}: {e}", level=messages.ERROR)

admin.site.register(Contact, ContactAdmin)