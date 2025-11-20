"""Utility for generating bonafide certificates with QR code, bank details and yearly fees."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import qrcode
import io
from datetime import datetime
from django.conf import settings
import hashlib
from students.models import AcademicYear


class BonafideCertificateGenerator:
    """Generate bonafide certificate PDF with security features."""

    def __init__(self, bonafide_request):
        self.request = bonafide_request
        self.student = bonafide_request.student
        self.width, self.height = A4

    def generate_qr_code(self):
        """Generate QR code for verification."""
        verification_url = f"{settings.ALLOWED_HOSTS[0]}/verify/{self.request.verification_code}"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(verification_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return ImageReader(buffer)

    def add_watermark(self, c):
        """Add watermark to prevent forgery."""
        c.saveState()
        c.setFont("Helvetica", 60)
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.translate(self.width / 2, self.height / 2)
        c.rotate(45)
        c.drawCentredString(0, 0, "ORIGINAL")
        c.restoreState()

    def add_digital_signature(self, c):
        """Add digital signature hash."""
        signature_data = f"{self.request.certificate_number}{self.student.register_number}{settings.BONAFIDE_SIGNATURE_KEY}"
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()

        c.saveState()
        c.setFont("Courier", 6)
        c.setFillColorRGB(0.7, 0.7, 0.7)
        c.drawString(50, 30, f"Digital Signature: {signature_hash[:64]}")
        c.restoreState()

    def generate_pdf(self):
        """Generate the complete bonafide certificate PDF."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        # Add watermark
        self.add_watermark(c)

        # Header with University Code
        y_position = self.height - 0.5 * inch
        c.setFont("Helvetica", 10)
        cert_parts = self.request.certificate_number.split('/')
        cert_year = datetime.now().year
        c.drawString(1 * inch, y_position, f"AURCC/Student Bonafide/Hostel/{cert_parts[-1] if len(cert_parts) > 0 else '0001'}/{cert_year}")
        c.drawRightString(self.width - 1 * inch, y_position, f"Date: {self.request.certificate_issued_date.strftime('%d.%m.%Y')}")
        
        # Title
        y_position -= 1.2 * inch
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(self.width / 2, y_position, "TO WHOMSOEVER IT MAY CONCERN")
        
        # Main content
        y_position -= 1 * inch
        c.setFont("Helvetica", 11)

        university_loc = getattr(settings, 'UNIVERSITY_LOCATION', 'Coimbatore')
        academic_year_obj = AcademicYear.get_current()
        current_year = academic_year_obj.current_year
        next_year = current_year + 1

        text_lines = [
            f"This is to certify that {self.student.name.upper()} is a Bonafide Student of this Regional Campus, {university_loc},",
            f"studying in {self.student.get_year_display_text()} {self.student.degree} {self.student.department.code} and staying in hostel during the",
            f"academic year {current_year}-{next_year}. The duration of their degree programme is from {self.student.admission_year} to {self.student.graduation_year}."
        ]
        
        line_height = 0.3 * inch
        for line in text_lines:
            c.drawString(1 * inch, y_position, line)
            y_position -= line_height
        
        # Fee structure section
        y_position -= 0.5 * inch
        c.setFont("Helvetica", 11)
        c.drawString(1 * inch, y_position, "The probable expenditure to be incurred for every year only if the students stay in the hostel will be as")
        y_position -= 0.3 * inch
        c.drawString(1 * inch, y_position, "follows.")
        
        # Get yearly fees for this student's hostel
        y_position -= 0.6 * inch
        hostel = self.student.hostel
        department = self.student.department
        
        if hostel and hostel.mess_fees_per_year > 0 and hostel.establishment_fees_per_year > 0:
            # Create fee table based on department course duration
            table_start_y = y_position
            table_x = 1 * inch
            col_widths = [1 * inch, 1.8 * inch, 2.5 * inch, 2.5 * inch]

            # Table headers
            c.setFont("Helvetica-Bold", 10)
            c.rect(table_x, table_start_y - 0.35 * inch, sum(col_widths), 0.35 * inch, stroke=1, fill=0)

            headers = ["S.No", "Year", "Establishment", "Mess (Approx)"]
            x_pos = table_x + 0.1 * inch
            for i, header in enumerate(headers):
                c.drawString(x_pos, table_start_y - 0.25 * inch, header)
                if i < len(headers) - 1:
                    c.line(x_pos + col_widths[i] - 0.1 * inch, table_start_y, x_pos + col_widths[i] - 0.1 * inch, table_start_y - 0.35 * inch)
                x_pos += col_widths[i]

            # Draw fee rows for each year based on department duration
            y_position = table_start_y - 0.35 * inch
            c.setFont("Helvetica", 10)
            course_years = department.course_duration_years if department else 4
            
            for year_num in range(1, course_years + 1):
                # Draw row rectangle
                c.rect(table_x, y_position - 0.35 * inch, sum(col_widths), 0.35 * inch, stroke=1, fill=0)
                
                # Draw vertical lines between columns
                for i in range(len(col_widths) - 1):
                    x_line = table_x + sum(col_widths[:i+1])
                    c.line(x_line, y_position, x_line, y_position - 0.35 * inch)
                
                # S.No
                c.drawString(table_x + 0.1 * inch, y_position - 0.25 * inch, str(year_num))
                
                # Year
                year_text = f"{year_num}{'st' if year_num == 1 else 'nd' if year_num == 2 else 'rd' if year_num == 3 else 'th'} Year"
                c.drawString(table_x + col_widths[0] + 0.1 * inch, y_position - 0.25 * inch, year_text)
                
                # Establishment Fee
                c.drawString(table_x + col_widths[0] + col_widths[1] + 0.1 * inch, y_position - 0.25 * inch, f"Rs.{hostel.establishment_fees_per_year}/-")
                
                # Mess Fee
                c.drawString(table_x + col_widths[0] + col_widths[1] + col_widths[2] + 0.1 * inch, y_position - 0.25 * inch, f"Rs.{hostel.mess_fees_per_year}/-")
                
                y_position -= 0.35 * inch

            # Total row
            c.rect(table_x, y_position - 0.35 * inch, sum(col_widths), 0.35 * inch, stroke=1, fill=0)
            
            # Draw vertical lines between columns for total row
            for i in range(len(col_widths) - 1):
                x_line = table_x + sum(col_widths[:i+1])
                c.line(x_line, y_position, x_line, y_position - 0.35 * inch)
            
            c.setFont("Helvetica-Bold", 10)
            c.drawString(table_x + 0.1 * inch, y_position - 0.25 * inch, "Total")

            total_establishment = hostel.establishment_fees_per_year * course_years
            total_mess = hostel.mess_fees_per_year * course_years

            c.drawString(table_x + col_widths[0] + col_widths[1] + 0.1 * inch, y_position - 0.25 * inch, f"Rs.{total_establishment}/-")
            c.drawString(table_x + col_widths[0] + col_widths[1] + col_widths[2] + 0.1 * inch, y_position - 0.25 * inch, f"Rs.{total_mess}/-")
            
            y_position -= 0.35 * inch
        else:
            # No fee data available
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(table_x + 0.1 * inch, y_position, "[Fee details will be updated by the administration]")
            y_position -= 0.5 * inch        # Bank Account Details section
        y_position -= 1 * inch
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1 * inch, y_position, "Bank Account Details:")
        
        from hostels.models import BankAccount
        bank_accounts = BankAccount.objects.filter(
            hostel=self.student.hostel,
            is_active=True
        ).order_by('account_type')
        
        # Create bank account table
        y_position -= 0.4 * inch
        bank_table_width = 6.5 * inch
        
        # Table rows
        for account in bank_accounts:
            # Bank Name row
            c.setFont("Helvetica-Bold", 10)
            c.rect(table_x, y_position - 0.35 * inch, 2 * inch, 0.35 * inch, stroke=1, fill=0)
            c.drawString(table_x + 0.1 * inch, y_position - 0.25 * inch, "Name of the Bank")
            
            c.setFont("Helvetica", 10)
            c.rect(table_x + 2 * inch, y_position - 0.35 * inch, bank_table_width - 2 * inch, 0.35 * inch, stroke=1, fill=0)
            c.drawString(table_x + 2.1 * inch, y_position - 0.25 * inch, f"{account.bank_name}, {account.branch_name}")
            
            y_position -= 0.35 * inch
            
            # IFSC Code row
            c.setFont("Helvetica-Bold", 10)
            c.rect(table_x, y_position - 0.35 * inch, 2 * inch, 0.35 * inch, stroke=1, fill=0)
            c.drawString(table_x + 0.1 * inch, y_position - 0.25 * inch, "IFSC Code")
            
            c.setFont("Helvetica", 10)
            c.rect(table_x + 2 * inch, y_position - 0.35 * inch, bank_table_width - 2 * inch, 0.35 * inch, stroke=1, fill=0)
            c.drawString(table_x + 2.1 * inch, y_position - 0.25 * inch, account.ifsc_code)
            
            y_position -= 0.35 * inch
            
            # Account Number row
            c.setFont("Helvetica-Bold", 10)
            c.rect(table_x, y_position - 0.35 * inch, 2 * inch, 0.35 * inch, stroke=1, fill=0)
            c.drawString(table_x + 0.1 * inch, y_position - 0.25 * inch, "Account Name & No")
            
            c.setFont("Helvetica", 10)
            c.rect(table_x + 2 * inch, y_position - 0.35 * inch, bank_table_width - 2 * inch, 0.35 * inch, stroke=1, fill=0)
            c.drawString(table_x + 2.1 * inch, y_position - 0.25 * inch, f"{account.account_name}    {account.account_number}")
            
            y_position -= 0.5 * inch
        
        # Note
        y_position -= 0.3 * inch
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(1 * inch, y_position, "Note: Amount to be transferred through NEFT/RTGS/Bank transfer to the respective Account.")
        
        # Signature section (if space permits)
        if y_position > 2.5 * inch:
            y_position = 2.2 * inch
            
            # Warden signature
            c.setFont("Helvetica", 10)
            c.drawString(1.5 * inch, y_position, "_" * 25)
            c.drawString(1.5 * inch, y_position - 0.25 * inch, "Deputy Warden")
            
            # Dean signature
            c.drawString(5 * inch, y_position, "_" * 25)
            c.drawString(5 * inch, y_position - 0.25 * inch, "Dean")
        
        # Add QR Code
        qr_image = self.generate_qr_code()
        qr_size = 1 * inch
        c.drawImage(qr_image, self.width - 1.5 * inch, 0.8 * inch, width=qr_size, height=qr_size)
        c.setFont("Helvetica", 7)
        c.drawString(self.width - 1.5 * inch, 0.6 * inch, "Scan to verify")
        
        # Add digital signature
        self.add_digital_signature(c)
        
        c.save()
        buffer.seek(0)
        return buffer

    def _get_pronoun(self):
        """Get possessive pronoun based on gender."""
        return "his" if self.student.gender == 'M' else "her"


def verify_certificate(verification_code):
    """Verify if a certificate is authentic."""
    from .models import BonafideRequest

    try:
        request = BonafideRequest.objects.get(verification_code=verification_code)

        # Verify digital signature
        signature_data = f"{request.certificate_number}{request.student.register_number}{settings.BONAFIDE_SIGNATURE_KEY}"
        expected_verification = hashlib.sha256(
            f"{request.request_id}{request.student.register_number}{settings.BONAFIDE_SIGNATURE_KEY}".encode()
        ).hexdigest()[:32]

        if verification_code != expected_verification:
            return {'valid': False, 'message': 'Invalid certificate'}

        return {
            'valid': True,
            'student_name': request.student.name,
            'register_number': request.student.register_number,
            'certificate_number': request.certificate_number,
            'issued_date': request.certificate_issued_date,
            'department': request.student.department.name,
            'year': request.student.get_year_display_text()
        }
    except BonafideRequest.DoesNotExist:
        return {'valid': False, 'message': 'Certificate not found'}
