from django.contrib import admin
from .models import Department, Student


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('register_number', 'name', 'department', 'current_year', 'gender', 'hostel')
    list_filter = ('department', 'current_year', 'gender', 'hostel')
    search_fields = ('register_number', 'name', 'email')
    readonly_fields = ('created_at', 'updated_at')
