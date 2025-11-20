import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_bonafide.settings')
django.setup()

from django.contrib.auth import authenticate
from accounts.models import User

# Test authentication
print("Testing authentication...")
username = 'admin'
password = 'admin123'

user = User.objects.filter(username=username).first()
if user:
    print(f"User found: {user.username}")
    print(f"User role: {user.role}")
    print(f"User active: {user.is_active}")
    print(f"Has password: {bool(user.password)}")
    
    # Test authenticate
    auth_user = authenticate(username=username, password=password)
    print(f"Authentication result: {auth_user}")
    
    if auth_user:
        print("✓ Authentication successful!")
    else:
        print("✗ Authentication failed!")
        # Try checking password directly
        if user.check_password(password):
            print("  But check_password works!")
        else:
            print("  check_password also fails")
else:
    print(f"User '{username}' not found")
