from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, DeanProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'must_change_password')
        read_only_fields = ('id', 'role')


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Password fields didn't match."})
        return attrs


class CreateWardenSerializer(serializers.ModelSerializer):
    """Serializer for creating warden accounts (Dean only)."""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 'role')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }
    
    def validate_role(self, value):
        if value not in ['warden', 'dean']:
            raise serializers.ValidationError("Can only create warden or dean accounts.")
        return value
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data['role'],
            must_change_password=True
        )
        return user


class DeanProfileSerializer(serializers.ModelSerializer):
    """Serializer for Dean profile."""
    
    class Meta:
        model = DeanProfile
        fields = ('id', 'name', 'designation', 'phone_number', 'email', 'updated_at')
        read_only_fields = ('id', 'updated_at')
