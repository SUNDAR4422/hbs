from django.db import models
from django.conf import settings
from datetime import datetime


class AcademicYear(models.Model):
    """Academic Year configuration (singleton pattern)."""
    
    current_year = models.IntegerField(help_text="Current academic year (e.g., 2024 for 2024-25)")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='academic_year_updates')
    
    class Meta:
        verbose_name = "Academic Year"
        verbose_name_plural = "Academic Year"
    
    def __str__(self):
        return f"{self.current_year}-{self.current_year + 1}"
    
    @classmethod
    def get_current(cls):
        """Get or create the current academic year."""
        obj, created = cls.objects.get_or_create(
            id=1,
            defaults={'current_year': datetime.now().year}
        )
        return obj


class Department(models.Model):
    """Department model."""

    code = models.CharField(max_length=10, unique=True, help_text="Department code (e.g., 106, 104, CSE)")
    name = models.CharField(max_length=200)
    course_duration_years = models.IntegerField(default=4, help_text="Duration of the course in years")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'departments'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name} ({self.course_duration_years} years)"
class Student(models.Model):
    """Student model linked to User account."""
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    
    YEAR_CHOICES = (
        (1, 'First Year'),
        (2, 'Second Year'),
        (3, 'Third Year'),
        (4, 'Fourth Year'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    register_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='students')
    degree = models.CharField(max_length=50)  # e.g., B.E., M.E., MBA
    current_year = models.IntegerField(choices=YEAR_CHOICES)
    admission_year = models.IntegerField()
    graduation_year = models.IntegerField()
    hostel = models.ForeignKey('hostels.Hostel', on_delete=models.SET_NULL, null=True, blank=True, related_name='residents')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students'
        ordering = ['register_number']
    
    def __str__(self):
        return f"{self.register_number} - {self.name}"
    
    def get_current_academic_year(self):
        """Calculate current year based on admission year."""
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Academic year starts in July
        if current_month >= 7:
            years_elapsed = current_year - self.admission_year + 1
        else:
            years_elapsed = current_year - self.admission_year
        
        return min(years_elapsed, 4)  # Cap at 4 years
    
    def get_year_display_text(self):
        """Get year as text (First Year, Second Year, etc.)."""
        year_map = {1: 'First', 2: 'Second', 3: 'Third', 4: 'Fourth'}
        return f"{year_map.get(self.current_year, 'First')} Year"
