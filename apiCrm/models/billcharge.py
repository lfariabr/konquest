from django.db import models

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
    customer_phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.quote_id} - {self.customer_name}"

class Meta:
    indexes = [
            models.Index(fields=['quote_id']),
            models.Index(fields=['customer_id']),
            models.Index(fields=['customer_phone']),
            models.Index(fields=['status']),
            models.Index(fields=['is_paid']),
            # Composite index for common query patterns
            models.Index(fields=['customer_id', 'is_paid'], name='idx_billcharge_customer_paid'),
        ]