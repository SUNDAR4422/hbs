from django.db import models
from django.conf import settings


class Hostel(models.Model):
    """Hostel model."""

    HOSTEL_TYPE_CHOICES = (
        ('boys', 'Boys Hostel'),
        ('girls', 'Girls Hostel'),
    )

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    hostel_type = models.CharField(max_length=10, choices=HOSTEL_TYPE_CHOICES)
    capacity = models.IntegerField(default=0)

    # Fee structure per year
    mess_fees_per_year = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    establishment_fees_per_year = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hostels'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_hostel_type_display()})"
    
    def get_current_occupancy(self):
        """Get current number of residents."""
        return self.residents.count()

    def get_available_capacity(self):
        """Get available capacity."""
        return self.capacity - self.get_current_occupancy()


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
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['hostel', 'year']
        ordering = ['hostel', 'year']

    def __str__(self):
        return f"{self.hostel.name} - Year {self.year}"    @property
    def total_fee(self):
        return self.establishment_fee + self.mess_fee


class Warden(models.Model):
    """Warden model linked to User account."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='warden_profile')
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='wardens')
    name = models.CharField(max_length=200, help_text="Full name with designation (e.g., Dr. M. Yuvaraju, Ph.D.)")
    designation = models.CharField(max_length=200, default="Deputy Warden")
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wardens'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.hostel.name}"
