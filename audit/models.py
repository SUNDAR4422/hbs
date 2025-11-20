from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """Audit log for tracking all system activities."""
    
    ACTION_CHOICES = (
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('CREATE_USER', 'Create User'),
        ('CREATE_BONAFIDE_REQUEST', 'Create Bonafide Request'),
        ('WARDEN_APPROVE', 'Warden Approve'),
        ('WARDEN_REJECT', 'Warden Reject'),
        ('DEAN_APPROVE', 'Dean Approve'),
        ('DEAN_REJECT', 'Dean Reject'),
        ('DOWNLOAD_BONAFIDE', 'Download Bonafide'),
        ('CREATE_HOSTEL', 'Create Hostel'),
        ('UPDATE_HOSTEL', 'Update Hostel'),
        ('CREATE_WARDEN_PROFILE', 'Create Warden Profile'),
        ('BULK_STUDENT_UPLOAD', 'Bulk Student Upload'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.timestamp}"
