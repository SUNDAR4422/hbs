from rest_framework import serializers
from .models import BonafideRequest, BonafideSettings
from students.serializers import StudentSerializer
from datetime import datetime, timedelta


class BonafideRequestSerializer(serializers.ModelSerializer):
    """Serializer for Bonafide Request."""
    student_details = StudentSerializer(source='student', read_only=True)
    warden_name = serializers.CharField(source='reviewed_by_warden.name', read_only=True)
    dean_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    
    class Meta:
        model = BonafideRequest
        fields = '__all__'
        read_only_fields = (
            'request_id', 'student', 'status', 'reviewed_by_warden', 'warden_review_date',
            'reviewed_by_dean', 'dean_review_date', 'certificate_number',
            'certificate_issued_date', 'certificate_file', 'verification_code'
        )
    
    def get_dean_name(self, obj):
        if obj.reviewed_by_dean:
            return f"{obj.reviewed_by_dean.first_name} {obj.reviewed_by_dean.last_name}"
        return None


class CreateBonafideRequestSerializer(serializers.ModelSerializer):
    """Serializer for creating bonafide request."""
    
    class Meta:
        model = BonafideRequest
        fields = ('reason', 'reason_description', 'attachment')
    
    def validate(self, data):
        """Check if student can submit new request based on cooldown period."""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required. Please log in again.")
        
        # Get student from request user
        try:
            student = request.user.student_profile
        except AttributeError:
            raise serializers.ValidationError(
                "Student profile not found. Please contact the administrator to set up your student profile."
            )
        
        # Get cooldown settings
        settings = BonafideSettings.get_settings()
        cooldown_days = settings.get_cooldown_days()
        
        # Skip cooldown check if disabled
        if cooldown_days == 0:
            return data
        
        # Check for recent approved requests
        cutoff_date = datetime.now() - timedelta(days=cooldown_days)
        recent_approved = BonafideRequest.objects.filter(
            student=student,
            status='dean_approved',
            dean_review_date__gte=cutoff_date
        ).order_by('-dean_review_date').first()
        
        if recent_approved:
            days_since_approval = (datetime.now() - recent_approved.dean_review_date.replace(tzinfo=None)).days
            days_remaining = cooldown_days - days_since_approval
            can_reapply_date = recent_approved.dean_review_date + timedelta(days=cooldown_days)
            
            raise serializers.ValidationError({
                'cooldown': True,
                'message': f'You can reapply after {settings.get_cooldown_period_display()} from your last approval',
                'days_remaining': days_remaining,
                'can_reapply_date': can_reapply_date.strftime('%Y-%m-%d'),
                'last_approved_date': recent_approved.dean_review_date.strftime('%Y-%m-%d')
            })
        
        return data


class WardenReviewSerializer(serializers.Serializer):
    """Serializer for warden review."""
    action = serializers.ChoiceField(choices=['approve', 'reject'], required=True)
    remarks = serializers.CharField(required=False, allow_blank=True)
    
    def validate_remarks(self, value):
        action = self.initial_data.get('action')
        if action == 'reject' and not value:
            raise serializers.ValidationError("Remarks are required for rejection")
        return value


class DeanReviewSerializer(serializers.Serializer):
    """Serializer for dean review."""
    action = serializers.ChoiceField(choices=['approve', 'reject'], required=True)
    remarks = serializers.CharField(required=False, allow_blank=True)


class BonafideSettingsSerializer(serializers.ModelSerializer):
    """Serializer for bonafide settings."""
    cooldown_display = serializers.CharField(source='get_cooldown_period_display', read_only=True)
    
    class Meta:
        model = BonafideSettings
        fields = ('id', 'cooldown_period', 'cooldown_display', 'updated_at', 'updated_by')
        read_only_fields = ('id', 'updated_at', 'updated_by')
