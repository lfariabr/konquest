from django.db import models

class Lead(models.Model):
    id = models.AutoField(primary_key=True)

    # CRM fields
    id_crm = models.CharField(max_length=100)
    name = models.CharField(max_length=150)
    email = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    source = models.CharField(max_length=100)
    store = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    customer_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField()

    # Extra cool fields to have
    utm_medium = models.CharField(max_length=100, null=True, blank=True)
    utm_campaign = models.CharField(max_length=100, null=True, blank=True)
    utm_content = models.CharField(max_length=100, null=True, blank=True)
    utm_search = models.CharField(max_length=100, null=True, blank=True)
    utm_term = models.CharField(max_length=100, null=True, blank=True)
    message = models.TextField(null=True, blank=True)

class Appointment(models.Model):
    id = models.AutoField(primary_key=True)

    # CRM fields
    id_crm = models.CharField(max_length=100)
    status_label = models.CharField(max_length=100)
    store_name = models.CharField(max_length=100)
    customer_id = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=100)
    procedure_name = models.CharField(max_length=100)
    procedure_group = models.CharField(max_length=100)
    employee_name = models.CharField(max_length=100)
    createdby_name = models.CharField(max_length=100)
    createdby_created_at = models.DateTimeField()
    appointment_date = models.DateTimeField()

class BillCharge(models.Model):
    quote_id = models.CharField(max_length=100)
    customer_id = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=200)
    customer_taxvat = models.CharField(max_length=50, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)    
    store_name = models.CharField(max_length=100)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    installments = models.IntegerField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    due_at = models.DateTimeField(blank=True, null=True)
    is_paid = models.BooleanField()
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    quote_items = models.TextField()  # Stores items as a semicolon-separated string

    def __str__(self):
        return f"{self.quote_id} - {self.customer_name}"