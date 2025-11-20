from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(generics.ListAPIView):
    """List audit logs (Dean and Warden only)."""
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_dean() or user.is_superuser:
            # Dean can see all logs
            return AuditLog.objects.all()
        elif user.is_warden():
            # Warden can only see logs related to their hostel
            try:
                warden = user.warden_profile
                # Get logs from students in warden's hostel and warden's own logs
                student_users = [s.user.id for s in warden.hostel.residents.all()]
                return AuditLog.objects.filter(user__id__in=student_users + [user.id])
            except:
                return AuditLog.objects.filter(user=user)
        else:
            # Students can only see their own logs
            return AuditLog.objects.filter(user=user)


class MyAuditLogListView(generics.ListAPIView):
    """List audit logs for the current user."""
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AuditLog.objects.filter(user=self.request.user)
