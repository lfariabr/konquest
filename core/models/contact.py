from django.db import models
from core.models.user import kUser
from django.utils import timezone
from apiCrm.models.lead import Lead
from apiCrm.models.appointment import Appointment
from apiCrm.models.billcharge import BillCharge
import logging

logger = logging.getLogger(__name__)

class Contact(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)
    relationship_tag = models.CharField(max_length=100, null=True, blank=True, default='')
    source = models.CharField(max_length=100, null=True, blank=True, default="Whatsapp")
    store = models.CharField(max_length=100, null=True, blank=True, default="CENTRAL")
    region = models.CharField(max_length=100, null=True, blank=True, default="São Paulo")
    user = models.ForeignKey(kUser, on_delete=models.CASCADE)
    
    # New fields for priority and availability
    available_to_queue = models.BooleanField(default=True, help_text="Whether this contact is available for queue processing")
    priority = models.IntegerField(default=5, help_text="Contact priority (1-5, where 1 is highest priority)")

    # Message counters
    botox_messages_sent = models.IntegerField(default=0, help_text="Number of Botox campaign messages sent")
    preenchimento_messages_sent = models.IntegerField(default=0, help_text="Number of Preenchimento campaign messages sent")
    last_message_sent_at = models.DateTimeField(null=True, blank=True)
    
    # External Info - CRM / Social Hub
    reference_code = models.CharField(max_length=100, null=True, blank=True)
    external_tag = models.CharField(max_length=255, null=True, blank=True, default="SEM TAGS")  # Map to 'Tags' column
    tag = models.CharField(max_length=255, null=True, blank=True)  # Internal tag (e.g., 'botox')
    status = models.CharField(max_length=255, null=True, blank=True, default="landing page")  # Default value

    # Lead tracking fields
    is_lead = models.BooleanField(default=False)
    lead_id = models.CharField(max_length=100, null=True, blank=True)
    lead_status = models.CharField(max_length=100, null=True, blank=True)
    lead_created_at = models.DateTimeField(null=True, blank=True)
    lead_last_checked = models.DateTimeField(null=True, blank=True)
    lead_check_count = models.IntegerField(default=0)
    store_lead = models.CharField(max_length=100, null=True, blank=True, default=None)

    # Appointment tracking fields
    is_appointment = models.BooleanField(default=False)
    appointment_id = models.CharField(max_length=100, null=True, blank=True)
    appointment_status = models.CharField(max_length=100, null=True, blank=True)
    appointment_created_at = models.DateTimeField(null=True, blank=True)
    appointment_last_checked = models.DateTimeField(null=True, blank=True)
    appointment_check_count = models.IntegerField(default=0)
    store_appointment = models.CharField(max_length=100, null=True, blank=True, default=None)
    
    # Bill Charge tracking fields
    is_bill_charge = models.BooleanField(default=False)
    bill_charge_id = models.CharField(max_length=100, null=True, blank=True)
    bill_charge_status = models.CharField(max_length=100, null=True, blank=True)
    bill_charge_created_at = models.DateTimeField(null=True, blank=True)
    bill_charge_last_checked = models.DateTimeField(null=True, blank=True)
    bill_charge_check_count = models.IntegerField(default=0)
    store_bill_charge = models.CharField(max_length=100, null=True, blank=True, default=None)
    bill_charge_installments = models.IntegerField(null=True, blank=True)
    bill_charge_total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bill_charge_total_history = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total amount of all bill charges for this contact")

    def __str__(self):
        lead_info = f" (Lead: {self.lead_status})" if self.is_lead else ""
        return f"{self.name} - {self.phone}{lead_info}"

    def clean_phone_number(self, phone):
        """Clean phone number to match CRM format (keep only digits)"""
        clean_phone = ''.join(filter(str.isdigit, phone))
        return clean_phone[-11:] if len(clean_phone) > 11 else clean_phone

    def check_if_lead_exists(self):
        """
        Check if this contact exists as a lead in the CRM.
        Returns the Lead object if found, None otherwise.
        Updates contact's lead status fields.
        """
        logger.info(f"Checking lead status for contact {self.id} ({self.phone})")
        
        # Update check tracking BEFORE checking status
        self.lead_last_checked = timezone.now()
        self.lead_check_count += 1
        self.save()

        try:
            # Direct phone number match since phones are already cleaned during import
            lead = Lead.objects.filter(phone=self.phone).first()
            
            if lead:
                logger.info(f"Found matching lead: {lead.id} for contact {self.id}")
                self._update_lead_status(lead)
                return lead
            
            logger.info(f"No matching lead found for contact {self.id}")
            self._clear_lead_status()
            return None
            
        except Lead.DoesNotExist:
            logger.info(f"No lead exists for contact {self.id}")
            self._clear_lead_status()
            return None
        except Exception as e:
            logger.error(f"Error checking lead for contact {self.id}: {str(e)}")
            return None

    def needs_lead_check(self, hours=24):
        """
        Check if this contact needs to be checked for lead status.
        Returns True if the contact hasn't been checked in the specified hours
        or has never been checked.
        """
        if not self.lead_last_checked:
            return True
        
        time_since_check = timezone.now() - self.lead_last_checked
        return time_since_check.total_seconds() > hours * 3600

    def get_lead_check_stats(self):
        """
        Get statistics about lead checks for this contact.
        """
        return {
            'total_checks': self.lead_check_count,
            'last_checked': self.lead_last_checked,
            'is_lead': self.is_lead,
            'lead_status': self.lead_status,
            'lead_age': (timezone.now() - self.lead_created_at).days if self.lead_created_at else None
        }

    def _update_lead_status(self, lead):
        """Update contact's lead status fields based on the found lead."""
        self.is_lead = True
        self.lead_id = lead.id_crm
        self.lead_status = lead.status
        self.lead_created_at = lead.created_at
        self.store_lead = lead.store
        self.save()

    def _clear_lead_status(self):
        """Clear lead status fields when no lead is found."""
        self.is_lead = False
        self.lead_id = None
        self.lead_status = None
        self.lead_created_at = None
        self.store_lead = None
        self.save()

    def check_if_appointment_exists(self):
        """
        Check if this contact exists as an appointment in the CRM.
        Returns the Appointment object if found, None otherwise.
        Updates contact's appointment status fields.
        """
        logger.info(f"Checking appointment status for contact {self.id} ({self.phone})")
        
        # Update check tracking BEFORE checking status
        self.appointment_last_checked = timezone.now()
        self.appointment_check_count += 1
        self.save()

        try:
            # Direct phone number match since phones are already cleaned during import
            appointment = Appointment.objects.filter(customer_phone=self.phone).first()
            
            if appointment:
                logger.info(f"Found matching appointment: {appointment.id} for contact {self.id}")
                self._update_appointment_status(appointment)
                return appointment
            
            logger.info(f"No matching appointment found for contact {self.id}")
            self._clear_appointment_status()
            return None
            
        except Appointment.DoesNotExist:
            logger.info(f"No appointment exists for contact {self.id}")
            self._clear_appointment_status()
            return None
        except Exception as e:
            logger.error(f"Error checking appointment for contact {self.id}: {str(e)}")
            return None

    def needs_appointment_check(self, hours=24):
        """
        Check if this contact needs to be checked for appointment status.
        Returns True if the contact hasn't been checked in the specified hours
        or has never been checked.
        """
        if not self.appointment_last_checked:
            return True

        time_since_check = timezone.now() - self.appointment_last_checked
        return time_since_check.total_seconds() > hours * 3600

    def get_appointment_check_stats(self):
        """
        Get statistics about appointment checks for this contact.
        """
        return {
            'total_checks': self.appointment_check_count,
            'last_checked': self.appointment_last_checked,
            'is_appointment': self.is_appointment,
            'appointment_status': self.appointment_status,
            'appointment_age': (timezone.now() - self.appointment_created_at).days if self.appointment_created_at else None
        }

    def _update_appointment_status(self, appointment):
        """Update contact's appointment status fields based on the found appointment."""
        self.is_appointment = True
        self.appointment_id = appointment.id_crm
        self.appointment_status = appointment.status_label
        self.appointment_created_at = appointment.appointment_date
        self.store_appointment = appointment.store_name
        self.save()

    def _clear_appointment_status(self):
        """Clear appointment status fields when no appointment is found."""
        self.is_appointment = False
        self.appointment_id = None
        self.appointment_status = None
        self.appointment_created_at = None
        self.store_appointment = None
        self.save()
    
    def check_if_bill_charges_exists(self):
        """
        Check if this contact has any bill charges in the system.
        Returns the BillCharge object if found, None otherwise.
        Updates contact's bill charge status fields.
        """
        logger.info(f"Checking bill charges for contact {self.id} ({self.phone})")
        
        # Update check tracking BEFORE checking status
        self.bill_charge_last_checked = timezone.now()
        self.bill_charge_check_count += 1
        self.save()

        try:
            # Get all bill charges for this contact
            all_charges = BillCharge.objects.filter(customer_phone=self.phone) # This is a problem, because customer_taxvat is not the phone number of customer...
            
            # Calculate total historical amount
            total_history = sum(charge.total_amount for charge in all_charges)
            self.bill_charge_total_history = total_history if total_history > 0 else None
            
            # Get the most recent bill charge
            bill_charge = all_charges.order_by('-due_at').first()
            
            if bill_charge:
                logger.info(f"Found matching bill charge: {bill_charge.id} for contact {self.id}")
                self.update_bill_charge_status(bill_charge)
                return bill_charge
            
            logger.info(f"No matching bill charge found for contact {self.id}")
            self.clear_bill_charge_status()
            return None
            
        except Exception as e:
            logger.error(f"Error checking bill charge for contact {self.id}: {str(e)}")
            return None

    def update_bill_charge_status(self, bill_charge):
        """Update contact's bill charge status fields based on the found bill charge."""
        self.is_bill_charge = True
        self.bill_charge_id = bill_charge.quote_id
        self.bill_charge_status = bill_charge.status
        self.bill_charge_created_at = bill_charge.due_at
        self.store_bill_charge = bill_charge.store_name
        self.bill_charge_installments = bill_charge.installments
        self.bill_charge_total_amount = bill_charge.total_amount
        self.save()

    def clear_bill_charge_status(self):
        """Clear bill charge status fields when no bill charge is found."""
        self.is_bill_charge = False
        self.bill_charge_id = None
        self.bill_charge_status = None
        self.bill_charge_created_at = None
        self.store_bill_charge = None
        self.bill_charge_installments = None
        self.bill_charge_total_amount = None
        self.bill_charge_total_history = None
        self.save()

    def needs_bill_charge_check(self, hours=24):
        """
        Check if this contact needs to be checked for bill charge status.
        Returns True if the contact hasn't been checked in the specified hours
        or has never been checked.
        """
        if not self.bill_charge_last_checked:
            return True
            
        time_since_check = timezone.now() - self.bill_charge_last_checked
        return time_since_check.total_seconds() > (hours * 3600)

    def get_bill_charge_check_stats(self):
        """
        Get statistics about bill charge checks for this contact.
        """
        return {
            'last_checked': self.bill_charge_last_checked,
            'check_count': self.bill_charge_check_count,
            'is_bill_charge': self.is_bill_charge,
            'bill_charge_status': self.bill_charge_status,
            'bill_charge_created_at': self.bill_charge_created_at,
            'store_bill_charge': self.store_bill_charge
        }

    @property
    def message_variables(self) -> dict:
        """
        Get message variables available for contact
        Returns:
            dict: Dictionary of message variables and their values
        """
        import logging
        logger = logging.getLogger(__name__)
        
        variables = {
            "[nome]": self.name.split()[0].capitalize() if self.name else "",
            "[unidade]": self.store.capitalize() if self.store else "",
        }
        
        logger.info(f"Basic variables for contact {self.id}: {variables}")
        
        # Add appointment-specific variables if this is an appointment contact
        if self.is_appointment and self.appointment_id:
            logger.info(f"Contact {self.id} is an appointment with id {self.appointment_id}")
            from apiCrm.models.appointment import Appointment
            from django.utils import timezone
            try:
                # Get appointment data
                appointment = Appointment.objects.filter(id_crm=self.appointment_id).first()
                if appointment:
                    logger.info(f"Found appointment: {appointment.id_crm} for contact {self.id}")
                    # Format date/time
                    if appointment.appointment_date:
                        # Convert UTC to BRT by subtracting 3 hours
                        brt_time = appointment.appointment_date - timezone.timedelta(hours=3)
                        variables.update({
                            "[data]": brt_time.strftime('%d/%m/%Y'),
                            "[hora]": brt_time.strftime('%H:%M'),
                        })
                    # Add address from store dictionary
                    from apiCrm.dicts.dict_address import dic_store_address
                    store_key = self.store.upper() if self.store else None
                    if store_key and store_key in dic_store_address:
                        variables["[address]"] = dic_store_address[store_key]
                        
                    # Add provider if available
                    if hasattr(appointment, 'employee_name'):
                        variables["[prestador]"] = appointment.employee_name.split()[0].capitalize()
                    
                    logger.info(f"Final variables for contact {self.id}: {variables}")
                else:
                    logger.error(f"No appointment found with id {self.appointment_id}")
                        
            except Exception as e:
                logger.error(f"Error getting appointment data for contact {self.id}: {str(e)}", exc_info=True)
                
        return variables

    class Meta:
        indexes = [models.Index(fields=['id'])]