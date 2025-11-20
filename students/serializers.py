from rest_framework import serializers
from .models import Student, Department
from accounts.models import User
from accounts.serializers import UserSerializer
from django.contrib.auth.hashers import make_password
from datetime import datetime


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""
    
    class Meta:
        model = Department
        fields = '__all__'


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model."""
    user = UserSerializer(read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    hostel_name = serializers.CharField(source='hostel.name', read_only=True)
    year_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = '__all__'
    
    def get_year_display(self, obj):
        return obj.get_year_display_text()


class BulkStudentUploadSerializer(serializers.Serializer):
    """Serializer for bulk student upload."""
    register_number = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=200)
    date_of_birth = serializers.CharField()
    gender = serializers.ChoiceField(choices=['M', 'F'])
    department_code = serializers.CharField(max_length=10)
    degree = serializers.CharField(max_length=50)
    current_year = serializers.IntegerField(min_value=1, max_value=4)
    admission_year = serializers.IntegerField()
    graduation_year = serializers.IntegerField()
    hostel_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    email = serializers.EmailField()

    def validate_date_of_birth(self, value):
        """Parse date from DD/MM/YYYY or YYYY-MM-DD format."""
        from datetime import datetime
        
        if isinstance(value, str):
            value = value.strip()
            
            # Try DD/MM/YYYY format first (preferred format)
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            
            raise serializers.ValidationError(f'Invalid date format: {value}. Use DD/MM/YYYY format.')
        
        raise serializers.ValidationError(f'Date must be a string in DD/MM/YYYY format.')
    
    def validate_department_code(self, value):
        try:
            Department.objects.get(code=value)
        except Department.DoesNotExist:
            raise serializers.ValidationError(f"Department with code '{value}' does not exist")
        return value
    
    def validate_hostel_code(self, value):
        if value:
            from hostels.models import Hostel
            try:
                Hostel.objects.get(code=value)
            except Hostel.DoesNotExist:
                raise serializers.ValidationError(f"Hostel with code '{value}' does not exist")
        return value
    
    def validate_register_number(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(f"Student with register number '{value}' already exists")
        return value
    
    def create_student(self):
        """Create student user and profile."""
        from hostels.models import Hostel

        # Create user account with DD/MM/YYYY password format
        user = User.objects.create(
            username=self.validated_data['register_number'],
            password=make_password(self.validated_data['date_of_birth'].strftime('%d/%m/%Y')),
            first_name=self.validated_data['name'].split()[0],
            last_name=' '.join(self.validated_data['name'].split()[1:]) if len(self.validated_data['name'].split()) > 1 else '',
            email=self.validated_data['email'],
            role='student',
            must_change_password=True
        )        # Get hostel if provided
        hostel = None
        if self.validated_data.get('hostel_code'):
            hostel = Hostel.objects.get(code=self.validated_data['hostel_code'])
        
        # Create student profile
        department = Department.objects.get(code=self.validated_data['department_code'])
        student = Student.objects.create(
            user=user,
            register_number=self.validated_data['register_number'],
            name=self.validated_data['name'],
            date_of_birth=self.validated_data['date_of_birth'],
            gender=self.validated_data['gender'],
            department=department,
            degree=self.validated_data['degree'],
            current_year=self.validated_data['current_year'],
            admission_year=self.validated_data['admission_year'],
            graduation_year=self.validated_data['graduation_year'],
            hostel=hostel,
            phone_number=self.validated_data.get('phone_number', ''),
            email=self.validated_data['email']
        )
        
        return student
