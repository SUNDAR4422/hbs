"""
Initial setup script for Hostel Bonafide System
Run this after migrations to populate initial data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from students.models import Department
from hostels.models import Hostel

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize system with default data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting system initialization...\n')

        # Create departments
        self.stdout.write('Creating departments...')
        departments_data = [
            ('CSE', 'Computer Science and Engineering'),
            ('ECE', 'Electronics and Communication Engineering'),
            ('EEE', 'Electrical and Electronics Engineering'),
            ('AI&DS', 'Artificial Intelligence and Data Science'),
            ('MBA', 'Master of Business Administration'),
        ]

        for code, name in departments_data:
            dept, created = Department.objects.get_or_create(
                code=code,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created department: {code}'))
            else:
                self.stdout.write(f'  Department {code} already exists')

        # Create sample hostels
        self.stdout.write('\nCreating sample hostels...')
        hostels_data = [
            {
                'name': 'Boys Hostel - Block A',
                'code': 'BH01',
                'hostel_type': 'boys',
                'capacity': 200,
                'mess_fees_per_year': 50000.00,
                'establishment_fees_per_year': 25000.00,
            },
            {
                'name': 'Girls Hostel - Block A',
                'code': 'GH01',
                'hostel_type': 'girls',
                'capacity': 150,
                'mess_fees_per_year': 50000.00,
                'establishment_fees_per_year': 25000.00,
            },
        ]

        for hostel_data in hostels_data:
            hostel, created = Hostel.objects.get_or_create(
                code=hostel_data['code'],
                defaults=hostel_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created hostel: {hostel_data["name"]}'))
            else:
                self.stdout.write(f'  Hostel {hostel_data["code"]} already exists')

        # Check for superuser
        self.stdout.write('\nChecking for superuser (Dean account)...')
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING(
                '\n⚠ No superuser found. Please create one using:'
            ))
            self.stdout.write('  python manage.py createsuperuser\n')
        else:
            self.stdout.write(self.style.SUCCESS('✓ Superuser exists'))

        self.stdout.write(self.style.SUCCESS('\n✓ System initialization complete!'))
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Create a superuser (if not already created): python manage.py createsuperuser')
        self.stdout.write('2. Start the development server: python manage.py runserver')
        self.stdout.write('3. Login as Dean and create warden accounts')
        self.stdout.write('4. Upload students via bulk upload feature')
