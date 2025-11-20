from django.contrib import admin
from .models import BonafideRequest


@admin.register(BonafideRequest)
class BonafideRequestAdmin(admin.ModelAdmin):
    list_display = (
        'request_id', 'student', 'reason', 'status',
        'warden_review_date', 'dean_review_date', 'created_at'
    )
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('request_id', 'student__register_number', 'student__name', 'certificate_number')
    readonly_fields = ('request_id', 'verification_code', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Request Information', {
            'fields': ('request_id', 'student', 'reason', 'reason_description', 'status')
        }),
        ('Warden Review', {
            'fields': ('reviewed_by_warden', 'warden_review_date', 'warden_remarks')
        }),
        ('Dean Review', {
            'fields': ('reviewed_by_dean', 'dean_review_date', 'dean_remarks')
        }),
        ('Certificate', {
            'fields': ('certificate_number', 'certificate_issued_date', 'certificate_file', 'verification_code')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
