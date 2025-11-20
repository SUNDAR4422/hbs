from rest_framework import serializers
from .models import Hostel, Warden, BankAccount
from accounts.serializers import UserSerializer


class BankAccountSerializer(serializers.ModelSerializer):
    """Serializer for BankAccount model."""
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    hostel_name = serializers.CharField(source='hostel.name', read_only=True)
    
    class Meta:
        model = BankAccount
        fields = '__all__'




class HostelSerializer(serializers.ModelSerializer):
    """Serializer for Hostel model."""
    current_occupancy = serializers.SerializerMethodField()
    available_capacity = serializers.SerializerMethodField()
    bank_accounts = BankAccountSerializer(many=True, read_only=True)

    class Meta:
        model = Hostel
        fields = '__all__'

    def get_current_occupancy(self, obj):
        return obj.get_current_occupancy()

    def get_available_capacity(self, obj):
        return obj.get_available_capacity()


class WardenSerializer(serializers.ModelSerializer):
    """Serializer for Warden model."""
    user = UserSerializer(read_only=True)
    hostel_name = serializers.CharField(source='hostel.name', read_only=True)

    class Meta:
        model = Warden
        fields = '__all__'


class CreateWardenProfileSerializer(serializers.ModelSerializer):
    """Serializer for creating warden profile."""
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Warden
        fields = ('user_id', 'hostel', 'name', 'phone_number', 'email')

    def create(self, validated_data):
        from accounts.models import User
        user = User.objects.get(id=validated_data.pop('user_id'))
        warden = Warden.objects.create(user=user, **validated_data)
        return warden