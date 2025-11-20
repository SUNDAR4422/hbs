"""Enhanced HTML-based PDF generator with digital signature and official logo."""

from weasyprint import HTML
from jinja2 import Template
import qrcode
import io
import base64
import hashlib
from datetime import datetime
from urllib.request import urlopen
import ssl 
from pathlib import Path
from students.models import AcademicYear
from accounts.models import DeanProfile
from django.conf import settings

class BonafideCertificateGenerator:
    """Generate professional bonafide certificate PDF."""

    def __init__(self, bonafide_request):
        self.request = bonafide_request
        self.student = bonafide_request.student

    def get_logo_base64(self):
        """Fetches the Anna University logo from a local file."""
        logo_img_path = Path(__file__).parent / "anna-university-logo-png.png"
        try:
            with open(logo_img_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                return f"data:image/png;base64,{encoded_string}"
        except Exception as e:
            print(f"Warning: Could not fetch logo. Error: {e}")
            return ""

    def generate_qr_code_base64(self):
        """Generate QR code as base64 image."""
        # Use the current website's domain for verification
        # If you have a settings.BASE_URL or similar, use that. Otherwise, hardcode your actual domain below.
        verification_url = f"https://{settings.ALLOWED_HOSTS[0]}/verify/{self.request.verification_code}" if hasattr(settings, 'ALLOWED_HOSTS') and settings.ALLOWED_HOSTS else f"http://localhost:8000/verify/{self.request.verification_code}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(verification_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_str = base64.b64encode(buffer.read()).decode()
        return f"data:image/png;base64,{img_str}"

    def generate_digital_signature(self):
        """Generate cryptographic signature hash."""
        signature_data = f"{self.request.certificate_number}{self.student.register_number}{self.request.verification_code}"
        return hashlib.sha256(signature_data.encode()).hexdigest()

    def get_context_data(self):
        """Prepare context data."""
        academic_year_obj = AcademicYear.get_current()
        current_year = academic_year_obj.current_year
        next_year = current_year + 1

        dean = DeanProfile.objects.filter(user__role='dean').first()
        
        warden = None
        if self.student.hostel:
            warden = self.student.hostel.wardens.first()

        establishment_account = None
        mess_account = None
        if self.student.hostel:
            establishment_account = self.student.hostel.bank_accounts.filter(
                account_type='establishment', is_active=True
            ).first()
            mess_account = self.student.hostel.bank_accounts.filter(
                account_type='mess', is_active=True
            ).first()

        # Calculate fees
        fee_rows = []
        total_establishment = 0
        total_mess = 0
        
        if self.student.hostel and self.student.department:
            course_years = self.student.department.course_duration_years
            establishment_fee = float(self.student.hostel.establishment_fees_per_year)
            mess_fee = float(self.student.hostel.mess_fees_per_year)
            
            year_names = ['First', 'Second', 'Third', 'Fourth', 'Fifth']
            for year_num in range(1, course_years + 1):
                year_name = year_names[year_num - 1] if year_num <= 5 else f"{year_num}th"
                fee_rows.append({
                    's_no': year_num,
                    'year': f"{year_name} Year",
                    'establishment': f"{establishment_fee:,.0f}",
                    'mess': f"{mess_fee:,.0f}"
                })
                total_establishment += establishment_fee
                total_mess += mess_fee

        cert_year = datetime.now().year
        cert_parts = self.request.certificate_number.split('/')
        cert_id = cert_parts[-1] if len(cert_parts) > 0 else '0001'
        formatted_cert_number = f"AURCC/HOSTEL/BONAFIDE/{cert_year}/{cert_id}"

        return {
            'student': self.student,
            'request': self.request,
            'dean': dean,
            'warden': warden,
            'establishment_account': establishment_account,
            'mess_account': mess_account,
            'current_year': current_year,
            'next_year': next_year,
            'fee_rows': fee_rows,
            'total_establishment': f"{total_establishment:,.0f}",
            'total_mess': f"{total_mess:,.0f}",
            'qr_code': self.generate_qr_code_base64(),
            'logo_img': self.get_logo_base64(),
            'digital_signature': self.generate_digital_signature(),
            'certificate_number': formatted_cert_number,
            'certificate_date': self.request.certificate_issued_date.strftime('%d.%m.%Y'),
            'degree_dept': f"{self.student.degree} {self.student.department.name}",
        }

    def generate_pdf(self):
        """Generate PDF from HTML template file."""
        context = self.get_context_data()
        
        # Read template file
        template_path = Path(__file__).parent / 'templates' / 'bonafide_certificate.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Render template with Jinja2
        template = Template(template_content)
        html_content = template.render(**context)
        
        # Generate PDF
        pdf = HTML(string=html_content).write_pdf()
        buffer = io.BytesIO(pdf)
        buffer.seek(0)
        return buffer


def verify_certificate(verification_code):
    """Verify certificate authenticity using verification code."""
    from bonafide.models import BonafideRequest
    
    try:
        request = BonafideRequest.objects.get(verification_code=verification_code)
        return {
            'valid': True,
            'certificate_number': request.certificate_number,
            'student_name': request.student.name,
            'register_number': request.student.register_number,
            'department': request.student.department.name,
            'issued_date': request.certificate_issued_date,
            'status': request.status
        }
    except BonafideRequest.DoesNotExist:
        return {'valid': False, 'error': 'Invalid verification code'}

