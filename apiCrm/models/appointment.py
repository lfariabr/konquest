from django.db import models

class Appointment(models.Model):
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

    def __str__(self):
        appointment_info = f" (Status: {self.status_label})" if self.status_label else ""
        return f"{self.customer_name} - {self.customer_phone}{appointment_info}"
    
    def check_if_appointment_is_evaluation(self):
        """
        Check if the appointment procedure_name contains
        the word "AVALIAÇÃO". If yes, return True.
        Otherwise, return False
        """
        if "AVALIAÇÃO" in self.procedure_name:
            return True
        return False