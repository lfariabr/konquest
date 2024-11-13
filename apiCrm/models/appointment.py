from django.db import models

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