from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Hostel, Warden, BankAccount
from .serializers import (
    HostelSerializer, WardenSerializer, CreateWardenProfileSerializer,
    BankAccountSerializer
)
from audit.utils import log_activity


class HostelListView(generics.ListAPIView):
    """List all hostels."""
    queryset = Hostel.objects.all()
    serializer_class = HostelSerializer
    permission_classes = [IsAuthenticated]


class HostelDetailView(generics.RetrieveUpdateAPIView):
    """Get and update hostel details (Dean only)."""
    queryset = Hostel.objects.all()
    serializer_class = HostelSerializer
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        if not request.user.is_dean() and not request.user.is_superuser:
            return Response(
                {'error': 'Only Dean can update hostel details'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        response = super().update(request, *args, **kwargs)
        log_activity(request.user, 'UPDATE_HOSTEL', f'Updated hostel: {self.get_object().name}')
        return response


class HostelCreateView(generics.CreateAPIView):
    """Create new hostel (Dean only)."""
    queryset = Hostel.objects.all()
    serializer_class = HostelSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not request.user.is_dean() and not request.user.is_superuser:
            return Response(
                {'error': 'Only Dean can create hostels'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        log_activity(request.user, 'CREATE_HOSTEL', f'Created hostel: {serializer.instance.name}')
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()
class WardenProfileView(generics.RetrieveUpdateAPIView):
    """Get and update warden profile."""
    serializer_class = WardenSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user.warden_profile


class CreateWardenProfileView(generics.CreateAPIView):
    """Create warden profile (Dean only)."""
    serializer_class = CreateWardenProfileSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not request.user.is_dean() and not request.user.is_superuser:
            return Response(
                {'error': 'Only Dean can create warden profiles'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            warden = serializer.save()
            
            log_activity(
                request.user,
                'CREATE_WARDEN_PROFILE',
                f'Created warden profile for: {warden.name}'
            )
            
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            import traceback
            print(f"Error creating warden: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': str(e), 'details': serializer.errors if 'serializer' in locals() else {}},
                status=status.HTTP_400_BAD_REQUEST
            )
class WardenListView(generics.ListAPIView):
    """List all wardens (Dean only)."""
    queryset = Warden.objects.all()
    serializer_class = WardenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_dean() and not self.request.user.is_superuser:
            return Warden.objects.none()
        return Warden.objects.all()


class WardenDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete warden profile (Dean only)."""
    queryset = Warden.objects.all()
    serializer_class = WardenSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        if not request.user.is_dean() and not request.user.is_superuser:
            return Response(
                {'error': 'Only Dean can update warden profiles'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        response = super().update(request, *args, **kwargs)
        log_activity(
            request.user,
            'UPDATE_WARDEN_PROFILE',
            f'Updated warden profile: {self.get_object().name}'
        )
        return response

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_dean() and not request.user.is_superuser:
            return Response(
                {'error': 'Only Dean can delete warden profiles'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        warden = self.get_object()
        warden_name = warden.name
        response = super().destroy(request, *args, **kwargs)
        log_activity(
            request.user,
            'DELETE_WARDEN_PROFILE',
            f'Deleted warden profile: {warden_name}'
        )
        return response


# Bank Account Management Views
class BankAccountListCreateView(generics.ListCreateAPIView):
    """List and create bank accounts (Dean only)."""
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from .models import BankAccount
        if not self.request.user.is_dean() and not self.request.user.is_superuser:
            return BankAccount.objects.none()
        
        hostel_id = self.request.query_params.get('hostel', None)
        if hostel_id:
            return BankAccount.objects.filter(hostel_id=hostel_id)
        return BankAccount.objects.all()
    
    def perform_create(self, serializer):
        if not self.request.user.is_dean() and not self.request.user.is_superuser:
            raise PermissionDenied('Only Dean can create bank accounts')
        
        bank_account = serializer.save()
        log_activity(
            self.request.user,
            'CREATE_BANK_ACCOUNT',
            f'Created bank account: {bank_account.account_type} for {bank_account.hostel.name}'
        )


class BankAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete bank account (Dean only)."""
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from .models import BankAccount
        if not self.request.user.is_dean() and not self.request.user.is_superuser:
            return BankAccount.objects.none()
        return BankAccount.objects.all()
    
    def perform_update(self, serializer):
        bank_account = serializer.save()
        log_activity(
            self.request.user,
            'UPDATE_BANK_ACCOUNT',
            f'Updated bank account: {bank_account.account_type} for {bank_account.hostel.name}'
        )
    
    def perform_destroy(self, instance):
        log_activity(
            self.request.user,
            'DELETE_BANK_ACCOUNT',
            f'Deleted bank account: {instance.account_type} for {instance.hostel.name}'
        )
        instance.delete()




