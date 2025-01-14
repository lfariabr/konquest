from django.contrib import admin
from django.contrib import messages
from django.db import models, transaction
from django.utils import timezone
import logging
import time
import csv
import tempfile
import os
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from datetime import datetime

# Import models with correct paths
from core.models.contact import Contact
from core.models.user import kUser
from core.models.userphone import UserPhone
from core.models.messagelog import MessageLogs
from core.models.message import Message
from apiCrm.models.lead import Lead
from apiCrm.models.appointment import Appointment
from apiCrm.models.billcharge import BillCharge

from core.forms.contact_upload import ContactCsvUploadForm
from core.resolvers.clean_phone_number import clean_phone_number
from core.resolvers.process_csv_files import process_csv_files

logger = logging.getLogger(__name__)

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
    exclude = ('user',)  # Hide user field from the form


    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user')
    
    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            try:
                kuser = kUser.objects.get(id=request.user.id)
                obj.user = kuser
            except kUser.DoesNotExist:
                logger.warning(f"User with id {request.user.id} does not exist")
                pass
        super().save_model(request, obj, form, change)

admin.site.register(UserPhone, UserPhoneAdmin)

class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'text', 'counter' ,'file_type', 'relationship_tag', 'created_at')
    search_fields = ('user__name', 'title', 'text', 'relationship_tag')
    list_filter = ('user', 'title', 'relationship_tag', 'created_at')
    exclude = ('user',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            try:
                kuser = kUser.objects.get(id=request.user.id)
                obj.user = kuser
            except kUser.DoesNotExist:
                logger.warning(f"User with id {request.user.id} does not exist")
                pass
        super().save_model(request, obj, form, change)

admin.site.register(Message, MessageAdmin)

class MessageLogsAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'sent_at', 'get_contact_phone_number', 'relationship_tag')
    search_fields = ('contact__phone', 'relationship_tag')
    list_filter = (
        ('sent_at', admin.DateFieldListFilter),
        'relationship_tag',
        'status'
    )
    ordering = ['-sent_at']
    list_per_page = 50
    date_hierarchy = 'sent_at'
    raw_id_fields = ('message', 'user', 'user_phone', 'contact')
    
    def get_contact_phone_number(self, obj): 
        return obj.contact.phone if obj.contact else '-'
    get_contact_phone_number.short_description = 'Contact Phone'
    get_contact_phone_number.admin_order_field = 'contact__phone'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'contact'
        ).defer(
            'message__text',
            'message__title',
            'user__name',
            'user_phone__phone_number'
        )

    def has_add_permission(self, request):
        return False  # Logs shouldn't be added manually

    def has_change_permission(self, request, obj=None):
        return False  # Logs shouldn't be modified

admin.site.register(MessageLogs, MessageLogsAdmin)


class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'created_at', 'source', 'relationship_tag',  
                    'store', 'region', 'external_tag', 'status', 
                    # Lead related data
                    'is_lead', 'lead_id', 'lead_status', 'lead_created_at', 'lead_last_checked', 'lead_check_count', 'store_lead',

                    # Appointment related data
                    'is_appointment', 'appointment_id', 'appointment_status', 'appointment_created_at', 
                    'appointment_last_checked', 'appointment_check_count', 'store_appointment',

                    # Bill Charge related data
                    'is_bill_charge', 'bill_charge_id', 'bill_charge_status', 'bill_charge_created_at', 
                    'bill_charge_last_checked', 'bill_charge_check_count', 'store_bill_charge', 
                    'formatted_bill_charge_amount', 'formatted_bill_charge_total_history',
                    )

    list_filter = ('source', 'store', 'relationship_tag', 'created_at')
    search_fields = ['phone']
    change_list_template = "admin/contacts_changelist.html"
    actions = ['check_leads', 'check_appointments', 'check_bill_charges'] # send_text_message_action, send_file_message_action
    ordering = ['-created_at']
    list_per_page = 500

    def formatted_bill_charge_amount(self, obj):
        if obj.bill_charge_total_amount:
            bill_charge_total_amount = obj.bill_charge_total_amount / 100
            return f"R$ {bill_charge_total_amount:,.2f}"
        return "-"
    formatted_bill_charge_amount.short_description = "Current Bill Amount"
    formatted_bill_charge_amount.admin_order_field = 'bill_charge_total_amount'

    def formatted_bill_charge_total_history(self, obj):
        if obj.bill_charge_total_history:
            bill_charge_total_history = obj.bill_charge_total_history / 100
            return f"R$ {bill_charge_total_history:,.2f}"
        return "-"
    formatted_bill_charge_total_history.short_description = "Total Bill History"
    formatted_bill_charge_total_history.admin_order_field = 'bill_charge_total_history'

    def check_leads(self, request, queryset):
        """Check selected contacts for leads using batch processing"""
        import time
        from django.db import transaction
        
        start_time = time.time()
        total = queryset.count()
        found = 0
        batch_size = 50
        
        self.message_user(request, f"Starting lead check for {total} contacts...", messages.INFO)
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = queryset[i:i + batch_size]
            
            # Update check tracking for batch
            now = timezone.now()
            with transaction.atomic():
                Contact.objects.filter(id__in=batch.values_list('id', flat=True)).update(
                    lead_last_checked=now,
                    lead_check_count=models.F('lead_check_count') + 1
                )
            
            # Get all phone numbers in this batch
            phones = batch.values_list('phone', flat=True)
            
            # Find matching leads in one query
            matching_leads = Lead.objects.filter(phone__in=phones)
            
            # Create a mapping of phone numbers to leads
            lead_map = {lead.phone: lead for lead in matching_leads}
            
            # Update contacts that have matching leads
            with transaction.atomic():
                for contact in batch:
                    lead = lead_map.get(contact.phone)
                    if lead:
                        found += 1
                        contact._update_lead_status(lead)
                    else:
                        contact._clear_lead_status()
            
            # Log progress
            progress = min(100, (i + batch_size) * 100 / total)
            elapsed = time.time() - start_time
            logger.info(f"Progress: {progress:.1f}% - Found {found} leads - Elapsed: {elapsed:.1f}s")
        
        elapsed = time.time() - start_time
        self.message_user(
            request,
            f"Checked {total} contacts in {elapsed:.1f}s. Found {found} leads.",
            messages.SUCCESS
        )

    def check_appointments(self, request, queryset):
        """Check selected contacts for appointments using batch processing"""
        import time
        from django.db import transaction
        
        start_time = time.time()
        total = queryset.count()
        found = 0
        batch_size = 50
        
        self.message_user(request, f"Starting appointment check for {total} contacts...", messages.INFO)
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = queryset[i:i + batch_size]
            
            # Update check tracking for batch
            now = timezone.now()
            with transaction.atomic():
                Contact.objects.filter(id__in=batch.values_list('id', flat=True)).update(
                    appointment_last_checked=now,
                    appointment_check_count=models.F('appointment_check_count') + 1
                )
            
            # Get all phone numbers in this batch
            phones = batch.values_list('phone', flat=True)
            
            # Find matching appointments in one query
            matching_appointments = Appointment.objects.filter(customer_phone__in=phones)
            
            # Create a mapping of phone numbers to appointments
            appointment_map = {appt.customer_phone: appt for appt in matching_appointments}
            
            # Update contacts that have matching appointments
            with transaction.atomic():
                for contact in batch:
                    appointment = appointment_map.get(contact.phone)
                    if appointment:
                        found += 1
                        contact._update_appointment_status(appointment)
                    else:
                        contact._clear_appointment_status()
            
            # Log progress
            progress = min(100, (i + batch_size) * 100 / total)
            elapsed = time.time() - start_time
            logger.info(f"Progress: {progress:.1f}% - Found {found} appointments - Elapsed: {elapsed:.1f}s")
        
        elapsed = time.time() - start_time
        self.message_user(
            request,
            f"Checked {total} contacts in {elapsed:.1f}s. Found {found} appointments.",
            messages.SUCCESS
        )

    def check_bill_charges(self, request, queryset):
        """Check selected contacts for bill charges using batch processing"""
        import time
        from django.db import transaction
        
        start_time = time.time()
        total = queryset.count()
        found = 0
        batch_size = 50
        
        self.message_user(request, f"Starting bill charge check for {total} contacts...", messages.INFO)
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = queryset[i:i + batch_size]
            
            # Update check tracking for batch
            now = timezone.now()
            with transaction.atomic():
                Contact.objects.filter(id__in=batch.values_list('id', flat=True)).update(
                    bill_charge_last_checked=now,
                    bill_charge_check_count=models.F('bill_charge_check_count') + 1
                )
            
            # Get all phone numbers in this batch
            phones = batch.values_list('phone', flat=True)
            
            # Find matching bill charges in one query
            matching_charges = BillCharge.objects.filter(customer_phone__in=phones)
            
            # Calculate total amounts per phone
            from django.db.models import Sum
            total_amounts = matching_charges.values('customer_phone').annotate(
                total_history=Sum('total_amount')
            )
            total_amount_map = {item['customer_phone']: item['total_history'] for item in total_amounts}
            
            # Create a mapping of phone numbers to most recent bill charges
            from django.db.models import Max
            latest_charges = matching_charges.values('customer_phone').annotate(
                latest_date=Max('due_at')
            )
            latest_map = {}
            for item in latest_charges:
                phone = item['customer_phone']
                latest_charge = matching_charges.filter(
                    customer_phone=phone,
                    due_at=item['latest_date']
                ).first()
                if latest_charge:
                    latest_map[phone] = latest_charge
            
            # Update contacts that have matching bill charges
            with transaction.atomic():
                for contact in batch:
                    bill_charge = latest_map.get(contact.phone)
                    total_history = total_amount_map.get(contact.phone)
                    
                    if bill_charge:
                        found += 1
                        contact.update_bill_charge_status(bill_charge)
                        contact.bill_charge_total_history = total_history
                        contact.save()
                    else:
                        contact.clear_bill_charge_status()
            
            # Log progress
            progress = min(100, (i + batch_size) * 100 / total)
            elapsed = time.time() - start_time
            logger.info(f"Progress: {progress:.1f}% - Found {found} bill charges - Elapsed: {elapsed:.1f}s")
        
        elapsed = time.time() - start_time
        self.message_user(
            request,
            f"Checked {total} contacts in {elapsed:.1f}s. Found {found} bill charges.",
            messages.SUCCESS
        )

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
            instagram_file = request.FILES.get('instagram_file')

            if not botox_file and not preenchimento_file and not instagram_file:
                self.message_user(request, "No files selected.", level=messages.ERROR)
                return HttpResponseRedirect(reverse('admin:core_contact_changelist'))

            # Process files
            for csv_file in [botox_file, preenchimento_file, instagram_file]:
                if csv_file:
                    self._process_csv_file(csv_file, created_date, request)

            self.message_user(request, "Contacts uploaded successfully.", level=messages.SUCCESS)
            return HttpResponseRedirect(reverse('admin:core_contact_changelist'))

        # Pass extra context for the upload form
        extra_context = extra_context or {}
        extra_context['form'] = ContactCsvUploadForm()
        return super().changelist_view(request, extra_context=extra_context)
    
    @staticmethod
    def get_relationship_tag(is_preenchimento, is_instagram, is_botox):
        if is_preenchimento:
            return 'Preenchimento'
        elif is_instagram:
            return 'Instagram'
        elif is_botox:
            return 'Botox'
        else:
            return None

    def _process_csv_file(self, csv_file, created_date, request):
        try:
            # Create temporary file to store the CSV data
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv') as temp_file:
                temp_file.write(csv_file.read().decode('utf-8'))
                temp_path = temp_file.name

            try:
                # Process CSV using process_csv_files
                is_preenchimento = 'preenchimento' in csv_file.name.lower()
                is_instagram = 'instagram' in csv_file.name.lower()
                is_botox = 'botox' in csv_file.name.lower()

                if is_preenchimento:
                    df_leads = process_csv_files(preenchimento_file_path=temp_path)
                
                elif is_instagram:
                    df_leads = process_csv_files(instagram_file_path=temp_path)
                
                elif is_botox:
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
                            relationship_tag=self.get_relationship_tag(is_preenchimento, is_instagram, is_botox),
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