from django.db import models
from .models import Hostel

class BankAccount(models.Model):
    """Model for managing hostel bank accounts"""
    ACCOUNT_TYPES = [
        ('establishment', 'Establishment'),
        ('mess', 'Mess'),
    ]
    
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='bank_accounts')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    bank_name = models.CharField(max_length=200)
    branch_name = models.CharField(max_length=200)
    ifsc_code = models.CharField(max_length=11)
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['hostel', 'account_type']
        ordering = ['hostel', 'account_type']
    
    def __str__(self):
        return f"{self.hostel.name} - {self.get_account_type_display()} - {self.account_number}"


class YearlyFee(models.Model):
    """Model for managing year-wise hostel fees"""
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='yearly_fees')
    year = models.IntegerField(help_text="Academic year (e.g., 1, 2, 3, 4)")
    establishment_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mess_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    academic_year = models.CharField(max_length=20, help_text="e.g., 2024-2025")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['hostel', 'year', 'academic_year']
        ordering = ['hostel', 'year']
    
    def __str__(self):
        return f"{self.hostel.name} - Year {self.year} ({self.academic_year})"
    
    @property
    def total_fee(self):
        return self.establishment_fee + self.mess_fee
