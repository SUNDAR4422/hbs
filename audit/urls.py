from django.urls import path
from .views import AuditLogListView, MyAuditLogListView

urlpatterns = [
    path('logs/', AuditLogListView.as_view(), name='audit_logs'),
    path('logs/my/', MyAuditLogListView.as_view(), name='my_audit_logs'),
]
