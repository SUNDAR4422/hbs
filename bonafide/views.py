from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.core.files.base import ContentFile
from django.http import FileResponse
from .models import BonafideRequest, BonafideSettings
from .serializers import (
    BonafideRequestSerializer, CreateBonafideRequestSerializer,
    WardenReviewSerializer, DeanReviewSerializer, BonafideSettingsSerializer
)
from .pdf_generator import BonafideCertificateGenerator, verify_certificate
from audit.utils import log_activity


class CreateBonafideRequestView(generics.CreateAPIView):
    """Create a new bonafide request (Student only)."""
    serializer_class = CreateBonafideRequestSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not request.user.is_student():
            return Response(
                {'error': 'Only students can create bonafide requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        student = request.user.student_profile
        
        # Check if student has a hostel assigned
        if not student.hostel:
            return Response(
                {'error': 'You must be assigned to a hostel before requesting a bonafide certificate. Please contact the Dean.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the hostel has a warden
        from hostels.models import Warden
        warden_exists = Warden.objects.filter(hostel=student.hostel).exists()
        if not warden_exists:
            return Response(
                {'error': 'Your hostel does not have a warden assigned yet. Please contact the Dean to assign a warden first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bonafide_request = serializer.save(student=student)

        log_activity(
            request.user,
            'CREATE_BONAFIDE_REQUEST',
            f'Created bonafide request: {bonafide_request.request_id}'
        )
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
class StudentBonafideRequestListView(generics.ListAPIView):
    """List all bonafide requests for logged-in student."""
    serializer_class = BonafideRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_student():
            return BonafideRequest.objects.none()
        return BonafideRequest.objects.filter(student=self.request.user.student_profile)


class WardenPendingRequestsView(generics.ListAPIView):
    """List pending bonafide requests for warden's hostel."""
    serializer_class = BonafideRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_warden():
            return BonafideRequest.objects.none()
        
        warden = self.request.user.warden_profile
        return BonafideRequest.objects.filter(
            student__hostel=warden.hostel,
            status='pending'
        )


class WardenReviewRequestView(APIView):
    """Warden approves or rejects bonafide request."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, request_id):
        if not request.user.is_warden():
            return Response(
                {'error': 'Only wardens can review requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            bonafide_request = BonafideRequest.objects.get(request_id=request_id)
        except BonafideRequest.DoesNotExist:
            return Response(
                {'error': 'Request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if warden's hostel matches student's hostel
        warden = request.user.warden_profile
        if bonafide_request.student.hostel != warden.hostel:
            return Response(
                {'error': 'You can only review requests from your hostel'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not bonafide_request.can_be_approved_by_warden():
            return Response(
                {'error': 'Request cannot be reviewed at this stage'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = WardenReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        remarks = serializer.validated_data.get('remarks', '')
        
        if action == 'approve':
            bonafide_request.status = 'warden_approved'
        else:
            bonafide_request.status = 'warden_rejected'
        
        bonafide_request.reviewed_by_warden = warden
        bonafide_request.warden_review_date = timezone.now()
        bonafide_request.warden_remarks = remarks
        bonafide_request.save()
        
        log_activity(
            request.user,
            f'WARDEN_{action.upper()}',
            f'{action.title()} bonafide request: {bonafide_request.request_id}'
        )
        
        return Response(
            BonafideRequestSerializer(bonafide_request).data,
            status=status.HTTP_200_OK
        )


class DeanPendingRequestsView(generics.ListAPIView):
    """List requests pending dean approval."""
    serializer_class = BonafideRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_dean() and not self.request.user.is_superuser:
            return BonafideRequest.objects.none()
        
        return BonafideRequest.objects.filter(status='warden_approved')


class DeanReviewRequestView(APIView):
    """Dean approves or rejects bonafide request."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, request_id):
        if not request.user.is_dean() and not request.user.is_superuser:
            return Response(
                {'error': 'Only dean can review requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            bonafide_request = BonafideRequest.objects.get(request_id=request_id)
        except BonafideRequest.DoesNotExist:
            return Response(
                {'error': 'Request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not bonafide_request.can_be_approved_by_dean():
            return Response(
                {'error': 'Request must be approved by warden first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = DeanReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        remarks = serializer.validated_data.get('remarks', '')
        
        if action == 'approve':
            bonafide_request.status = 'dean_approved'
            bonafide_request.certificate_number = bonafide_request.generate_certificate_number()
            bonafide_request.verification_code = bonafide_request.generate_verification_code()
            bonafide_request.certificate_issued_date = timezone.now()
            
            # Generate PDF
            pdf_generator = BonafideCertificateGenerator(bonafide_request)
            pdf_buffer = pdf_generator.generate_pdf()
            
            # Save PDF to file field
            pdf_filename = f"bonafide_{bonafide_request.certificate_number.replace('/', '_')}.pdf"
            bonafide_request.certificate_file.save(
                pdf_filename,
                ContentFile(pdf_buffer.read()),
                save=False
            )
        else:
            bonafide_request.status = 'dean_rejected'
        
        bonafide_request.reviewed_by_dean = request.user
        bonafide_request.dean_review_date = timezone.now()
        bonafide_request.dean_remarks = remarks
        bonafide_request.save()
        
        log_activity(
            request.user,
            f'DEAN_{action.upper()}',
            f'{action.title()} bonafide request: {bonafide_request.request_id}'
        )
        
        return Response(
            BonafideRequestSerializer(bonafide_request).data,
            status=status.HTTP_200_OK
        )


class DownloadBonafideView(APIView):
    """Download bonafide certificate PDF."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, request_id):
        try:
            bonafide_request = BonafideRequest.objects.get(request_id=request_id)
        except BonafideRequest.DoesNotExist:
            return Response(
                {'error': 'Request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        if request.user.is_student():
            if bonafide_request.student.user != request.user:
                return Response(
                    {'error': 'You can only download your own certificates'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif not (request.user.is_warden() or request.user.is_dean() or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if bonafide_request.status != 'dean_approved' or not bonafide_request.certificate_file:
            return Response(
                {'error': 'Certificate not yet generated'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        log_activity(
            request.user,
            'DOWNLOAD_BONAFIDE',
            f'Downloaded bonafide certificate: {bonafide_request.certificate_number}'
        )
        
        return FileResponse(
            bonafide_request.certificate_file.open('rb'),
            as_attachment=True,
            filename=f"bonafide_{bonafide_request.certificate_number.replace('/', '_')}.pdf"
        )


class VerifyBonafideView(APIView):
    """Verify bonafide certificate authenticity."""
    permission_classes = []
    
    def get(self, request, verification_code):
        result = verify_certificate(verification_code)
        return Response(result)


class AllBonafideRequestsView(generics.ListAPIView):
    """List all bonafide requests (Dean and Warden)."""
    serializer_class = BonafideRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_dean() or user.is_superuser:
            return BonafideRequest.objects.all()
        elif user.is_warden():
            warden = user.warden_profile
            return BonafideRequest.objects.filter(student__hostel=warden.hostel)
        else:
            return BonafideRequest.objects.none()


class BonafideSettingsView(APIView):
    """Get and update bonafide settings (Dean only)."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current settings."""
        settings = BonafideSettings.get_settings()
        serializer = BonafideSettingsSerializer(settings)
        return Response(serializer.data)
    
    def put(self, request):
        """Update settings (Dean only)."""
        if not request.user.is_dean() and not request.user.is_superuser:
            return Response(
                {'error': 'Only dean can update settings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        settings = BonafideSettings.get_settings()
        serializer = BonafideSettingsSerializer(settings, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save(updated_by=request.user)
            
            log_activity(
                request.user,
                'UPDATE_BONAFIDE_SETTINGS',
                f'Updated cooldown period to {settings.get_cooldown_period_display()}'
            )
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
