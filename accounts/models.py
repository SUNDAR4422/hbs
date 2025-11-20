from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    """Custom User model with role-based access control."""
    
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('warden', 'Warden'),
        ('dean', 'Dean'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    must_change_password = models.BooleanField(default=True)
    email = models.EmailField(blank=True, null=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        # Ensure empty email is saved as None instead of empty string
        if self.email == '':
            self.email = None
        super().save(*args, **kwargs)
    
    def is_student(self):
        return self.role == 'student'
    
    def is_warden(self):
        return self.role == 'warden'
    
    def is_dean(self):
        return self.role == 'dean'


class DeanProfile(models.Model):
    """Dean profile with contact details for certificates."""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dean_profile')
    name = models.CharField(max_length=200, help_text="Full name with designation (e.g., Dr. M. Saravanakumar, Ph.D.)")
    designation = models.CharField(max_length=200, default="Dean-Regional Campus (Warden)")
    phone_number = models.CharField(max_length=15, help_text="Contact phone number")
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dean_profiles'
    
    def __str__(self):
        return self.name
