from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, DeanProfile
from .serializers import (
    UserSerializer, LoginSerializer, ChangePasswordSerializer, CreateWardenSerializer,
    DeanProfileSerializer
)
from audit.utils import log_activity

# TEST: This should print when module loads
print("=" * 80)
print("ACCOUNTS VIEWS.PY MODULE LOADED - NEW CODE IS ACTIVE!")
print("=" * 80)


class LoginView(APIView):
    """Handle user login and return JWT tokens."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Check for role in request (for student login)
        requested_role = request.data.get('role')
        print("=" * 50)
        print("LOGIN ATTEMPT RECEIVED")
        print(f"Request data: {request.data}")
        
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        print(f"Username: {username}")
        print(f"Password length: {len(password)}")
        
        # Check if user exists
        from .models import User
        try:
            db_user = User.objects.get(username=username)
            print(f"User found in DB: {db_user.username}, active: {db_user.is_active}")
            print(f"Password check: {db_user.check_password(password)}")
        except User.DoesNotExist:
            print(f"User {username} NOT FOUND in database")
        
        user = authenticate(username=username, password=password)
        # If role is specified (from student login), enforce role match
        if requested_role:
            if not user or user.role != requested_role:
                return Response(
                    {'error': f'Access denied. Only {requested_role}s can login here.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        print(f"Authentication result: {user}")
        print("=" * 50)
        
        if user is None:
            return Response(
                {'error': 'Invalid username or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'Account is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        log_activity(user, 'LOGIN', 'User logged in successfully')
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'must_change_password': user.must_change_password
        })


class LogoutView(APIView):
    """Handle user logout."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        log_activity(request.user, 'LOGOUT', 'User logged out')
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """Allow users to change their password."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Current password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.must_change_password = False
        user.save()
        
        log_activity(user, 'PASSWORD_CHANGE', 'Password changed successfully')
        
        return Response({'message': 'Password changed successfully'})


class MeView(APIView):
    """Get current user information."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class CreateWardenView(generics.CreateAPIView):
    """Create warden accounts (Dean only)."""
    serializer_class = CreateWardenSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Only dean can create wardens
        if not request.user.is_dean() and not request.user.is_superuser:
            return Response(
                {'error': 'Only Dean can create warden accounts'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
            log_activity(
                request.user,
                'CREATE_USER',
                f'Created {user.get_role_display()} account: {user.username}'
            )
            
            # Use UserSerializer for response to include id field
            response_serializer = UserSerializer(user)
            headers = self.get_success_headers(response_serializer.data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            import traceback
            print(f"Error creating warden user: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': str(e), 'details': serializer.errors if 'serializer' in locals() else {}},
                status=status.HTTP_400_BAD_REQUEST
            )
class ListWardensView(generics.ListAPIView):
    """List all wardens (Dean only)."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only dean can view wardens list
        if not self.request.user.is_dean() and not self.request.user.is_superuser:
            return User.objects.none()
        return User.objects.filter(role='warden')


class WardenDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete warden user (Dean only)."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.filter(role='warden')

    def update(self, request, *args, **kwargs):
        if not request.user.is_dean() and not request.user.is_superuser:
            return Response(
                {'error': 'Only Dean can update warden accounts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        response = super().update(request, *args, **kwargs)
        log_activity(
            request.user,
            'UPDATE_USER',
            f'Updated warden account: {self.get_object().username}'
        )
        return response

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_dean() and not request.user.is_superuser:
            return Response(
                {'error': 'Only Dean can delete warden accounts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        warden = self.get_object()
        username = warden.username
        response = super().destroy(request, *args, **kwargs)
        log_activity(
            request.user,
            'DELETE_USER',
            f'Deleted warden account: {username}'
        )
        return response


class DeanProfileView(APIView):
    """Get and update Dean profile (Dean only)."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current dean profile or create if doesn't exist."""
        try:
            profile = DeanProfile.objects.filter(user__role='dean').first()
            if not profile and (request.user.is_dean() or request.user.is_superuser):
                # Create default profile for the dean user
                profile = DeanProfile.objects.create(
                    user=request.user,
                    name=f"{request.user.first_name} {request.user.last_name}",
                    designation="Dean-Regional Campus (Warden)",
                    phone_number="",
                    email=request.user.email or ""
                )
            
            if profile:
                serializer = DeanProfileSerializer(profile)
                return Response(serializer.data)
            else:
                return Response({'error': 'Dean profile not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request):
        """Update dean profile (Dean only)."""
        if not (request.user.is_dean() or request.user.is_superuser):
            return Response(
                {'error': 'Only Dean can update profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            profile = DeanProfile.objects.filter(user__role='dean').first()
            if not profile:
                profile = DeanProfile.objects.create(user=request.user)
            
            serializer = DeanProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                log_activity(
                    request.user,
                    'UPDATE',
                    f'Updated Dean profile: {serializer.data["name"]}',
                    request
                )
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
