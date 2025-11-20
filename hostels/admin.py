from django.contrib import admin
from .models import Hostel, Warden


@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'hostel_type', 'capacity', 'mess_fees_per_year', 'establishment_fees_per_year')
    list_filter = ('hostel_type',)
    search_fields = ('name', 'code')


@admin.register(Warden)
class WardenAdmin(admin.ModelAdmin):
    list_display = ('name', 'hostel', 'email', 'phone_number')
    list_filter = ('hostel',)
    search_fields = ('name', 'email')
