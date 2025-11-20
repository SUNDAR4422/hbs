from django.db import models
from django.conf import settings
from students.models import Student
from hostels.models import Warden
import uuid


class BonafideSettings(models.Model):
    """System-wide bonafide settings managed by dean."""
    
    COOLDOWN_CHOICES = (
        ('disabled', 'Disabled (No Cooldown)'),
        ('1_month', '1 Month'),
        ('3_months', '3 Months'),
        ('6_months', '6 Months'),
        ('1_year', '1 Year'),
    )
    
    cooldown_period = models.CharField(
        max_length=20, 
        choices=COOLDOWN_CHOICES, 
        default='3_months',
        help_text='Period after approval before student can reapply'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bonafide_settings_updates'
    )
    
    class Meta:
        db_table = 'bonafide_settings'
        verbose_name = 'Bonafide Settings'
        verbose_name_plural = 'Bonafide Settings'
    
    def __str__(self):
        return f"Cooldown Period: {self.get_cooldown_period_display()}"
    
    @classmethod
    def get_settings(cls):
        """Get or create settings instance."""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
    
    def get_cooldown_days(self):
        """Convert cooldown period to days."""
        if self.cooldown_period == 'disabled':
            return 0
        cooldown_map = {
            '1_month': 30,
            '3_months': 90,
            '6_months': 180,
            '1_year': 365,
        }
        return cooldown_map.get(self.cooldown_period, 90)


class BonafideRequest(models.Model):
    """Bonafide Certificate Request model."""
    
    STATUS_CHOICES = (
        ('pending', 'Pending with Warden'),
        ('warden_approved', 'Approved by Warden'),
        ('warden_rejected', 'Rejected by Warden'),
        ('dean_approved', 'Approved by Dean'),
        ('dean_rejected', 'Rejected by Dean'),
    )
    
    REASON_CHOICES = (
        ('bank_loan', 'Bank Loan'),
        ('scholarship', 'Scholarship'),
        ('passport', 'Passport Application'),
        ('visa', 'Visa Application'),
        ('identity_proof', 'Identity Proof'),
        ('other', 'Other'),
    )
    
    request_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='bonafide_requests')
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    reason_description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Supporting documents (optional)
    attachment = models.FileField(upload_to='bonafide_attachments/', null=True, blank=True)
    
    # Warden review
    reviewed_by_warden = models.ForeignKey(
        Warden,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_requests'
    )
    warden_review_date = models.DateTimeField(null=True, blank=True)
    warden_remarks = models.TextField(blank=True)
    
    # Dean review
    reviewed_by_dean = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dean_reviewed_requests'
    )
    dean_review_date = models.DateTimeField(null=True, blank=True)
    dean_remarks = models.TextField(blank=True)
    
    # Certificate details
    certificate_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    certificate_issued_date = models.DateTimeField(null=True, blank=True)
    certificate_file = models.FileField(upload_to='bonafide_certificates/', null=True, blank=True)
    verification_code = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bonafide_requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.register_number} - {self.get_reason_display()} ({self.get_status_display()})"
    
    def can_be_approved_by_warden(self):
        """Check if request can be approved by warden."""
        return self.status == 'pending'
    
    def can_be_approved_by_dean(self):
        """Check if request can be approved by dean."""
        return self.status == 'warden_approved'
    
    def generate_certificate_number(self):
        """Generate unique certificate number."""
        from datetime import datetime
        year = datetime.now().year
        count = BonafideRequest.objects.filter(
            certificate_issued_date__year=year
        ).count() + 1
        return f"BC/{year}/{count:04d}"
    
    def generate_verification_code(self):
        """Generate verification code for QR."""
        import hashlib
        from django.conf import settings
        
        data = f"{self.request_id}{self.student.register_number}{settings.BONAFIDE_SIGNATURE_KEY}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
