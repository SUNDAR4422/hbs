"""Improved PDF generator matching the provided template."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import qrcode
import io
from datetime import datetime
from django.conf import settings
import hashlib
from students.models import AcademicYear
from accounts.models import DeanProfile


class BonafideCertificateGenerator:
    """Generate bonafide certificate PDF with improved design."""

    def __init__(self, bonafide_request):
        self.request = bonafide_request
        self.student = bonafide_request.student
        self.width, self.height = A4

    def generate_qr_code(self):
        """Generate QR code for verification."""
        # Use the actual verification URL with the code
        verification_data = f"Certificate: {self.request.certificate_number}\nStudent: {self.student.register_number}\nName: {self.student.name}\nUnique ID: {self.request.verification_code}"
        
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(verification_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return ImageReader(buffer)

    def draw_header(self, c):
        """Draw university header with logo."""
        y_position = self.height - 0.8 * inch
        
        # Draw university logo placeholder (if available)
        # You can add actual logo image here
        c.setFillColorRGB(0.2, 0.3, 0.6)
        c.circle(1.2 * inch, y_position, 0.4 * inch, stroke=1, fill=0)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(1.2 * inch, y_position - 0.08 * inch, "ANNA")
        c.drawCentredString(1.2 * inch, y_position - 0.2 * inch, "UNIVERSITY")
        
        # University name
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(self.width / 2, y_position + 0.1 * inch, "ANNA UNIVERSITY")
        
        c.setFont("Helvetica", 11)
        c.drawCentredString(self.width / 2, y_position - 0.2 * inch, "Regional Campus Coimbatore - Hostel")

    def draw_contact_details(self, c):
        """Draw Dean and Deputy Warden contact details."""
        y_position = self.height - 1.5 * inch
        
        # Get dean profile
        dean = DeanProfile.objects.filter(user__role='dean').first()
        warden = None
        if self.student.hostel:
            warden = self.student.hostel.wardens.first()
        
        # Dean details (left)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1 * inch, y_position, dean.name if dean else "Dr. M. Saravanakumar, Ph.D.")
        c.setFont("Helvetica", 8)
        c.drawString(1 * inch, y_position - 0.15 * inch, dean.designation if dean else "Dean-Regional Campus (Warden)")
        c.drawString(1 * inch, y_position - 0.3 * inch, f"Ph: {dean.phone_number if dean and dean.phone_number else '0422 2200209'}")
        
        # Deputy Warden details (right)
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(self.width - 1 * inch, y_position, warden.name if warden else "Dr. M. Yuvaraju, Ph.D.")
        c.setFont("Helvetica", 8)
        c.drawRightString(self.width - 1 * inch, y_position - 0.15 * inch, warden.designation if warden else "Deputy Warden")

    def draw_certificate_number_and_date(self, c):
        """Draw certificate number and date."""
        y_position = self.height - 2.2 * inch
        
        # Certificate number (left)
        c.setFont("Helvetica", 9)
        cert_parts = self.request.certificate_number.split('/')
        cert_year = datetime.now().year
        c.drawString(1 * inch, y_position, f"AURCC/Student Bonafide/Hostel/{cert_parts[-1] if len(cert_parts) > 0 else '0001'}/{cert_year}")
        
        # Date (right)
        c.drawRightString(self.width - 1 * inch, y_position, f"Date: {self.request.certificate_issued_date.strftime('%d.%m.%Y')}")

    def draw_title(self, c):
        """Draw certificate title."""
        y_position = self.height - 2.7 * inch
        
        c.setFont("Helvetica-Bold", 14)
        c.setFillColorRGB(0, 0, 0.6)
        c.drawCentredString(self.width / 2, y_position, "TO WHOMSOEVER IT MAY CONCERN")
        c.setFillColorRGB(0, 0, 0)
        
        # Underline
        text_width = c.stringWidth("TO WHOMSOEVER IT MAY CONCERN", "Helvetica-Bold", 14)
        c.line((self.width - text_width) / 2, y_position - 0.05 * inch, 
               (self.width + text_width) / 2, y_position - 0.05 * inch)

    def draw_main_content(self, c):
        """Draw main certificate content."""
        y_position = self.height - 3.4 * inch
        
        academic_year_obj = AcademicYear.get_current()
        current_year = academic_year_obj.current_year
        next_year = current_year + 1
        
        # Paragraph text with proper formatting
        c.setFont("Helvetica", 11)
        
        # Line 1
        line1 = f"This is to certify that {self.student.name.upper()} is a Bonafide Student of this Regional Campus, Coimbatore,"
        c.drawString(1 * inch, y_position, line1)
        
        # Line 2
        y_position -= 0.25 * inch
        degree_dept = f"{self.student.degree} {self.student.department.code}" if self.student.department.code else self.student.degree
        line2 = f"studying in {self.student.get_year_display_text()} {degree_dept} and staying in hostel during the"
        c.drawString(1 * inch, y_position, line2)
        
        # Line 3
        y_position -= 0.25 * inch
        line3 = f"academic year {current_year}-{next_year}. The duration of their degree programme is from {self.student.admission_year} to {self.student.graduation_year}."
        c.drawString(1 * inch, y_position, line3)
        
        return y_position

    def draw_fee_table(self, c, start_y):
        """Draw expenditure table."""
        y_position = start_y - 0.6 * inch
        
        c.setFont("Helvetica", 11)
        c.drawString(1 * inch, y_position, "The probable expenditure to be incurred for every year only if the students stay in the hostel will be as")
        y_position -= 0.25 * inch
        c.drawString(1 * inch, y_position, "follows.")
        
        y_position -= 0.4 * inch
        
        # Get fee details
        hostel = self.student.hostel
        department = self.student.department
        
        if hostel and department:
            course_years = department.course_duration_years
            establishment_fee = float(hostel.establishment_fees_per_year)
            mess_fee = float(hostel.mess_fees_per_year)
            
            # Create table data
            table_data = [
                ['S.No', 'Year', 'Establishment', 'Mess (Approx)'],
                ['Total', '', 'Rs.0/-', 'Rs.0/-']
            ]
            
            # Insert year-wise rows
            for year_num in range(1, course_years + 1):
                year_name = ['First', 'Second', 'Third', 'Fourth', 'Fifth'][year_num - 1] if year_num <= 5 else f"{year_num}th"
                table_data.insert(year_num, [
                    str(year_num),
                    f"{year_name} Year",
                    f"Rs.{establishment_fee:,.0f}/-" if establishment_fee > 0 else "Rs.0/-",
                    f"Rs.{mess_fee:,.0f}/-" if mess_fee > 0 else "Rs.0/-"
                ])
            
            # Update totals
            total_establishment = establishment_fee * course_years
            total_mess = mess_fee * course_years
            table_data[-1] = ['Total', '', 
                            f"Rs.{total_establishment:,.0f}/-" if total_establishment > 0 else "Rs.0/-",
                            f"Rs.{total_mess:,.0f}/-" if total_mess > 0 else "Rs.0/-"]
        else:
            # Default empty table
            table_data = [
                ['S.No', 'Year', 'Establishment', 'Mess (Approx)'],
                ['Total', '', 'Rs.0/-', 'Rs.0/-']
            ]
        
        # Create and style table
        table = Table(table_data, colWidths=[0.8 * inch, 2 * inch, 2 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8F0FE')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        # Draw table
        table.wrapOn(c, self.width, self.height)
        table.drawOn(c, 1 * inch, y_position - table._height)
        
        return y_position - table._height

    def draw_bank_details(self, c, start_y):
        """Draw bank account details table."""
        y_position = start_y - 0.5 * inch
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1 * inch, y_position, "Bank Account Details:")
        
        y_position -= 0.3 * inch
        
        # Get bank accounts
        hostel = self.student.hostel
        establishment_account = None
        mess_account = None
        
        if hostel:
            establishment_account = hostel.bank_accounts.filter(account_type='establishment').first()
            mess_account = hostel.bank_accounts.filter(account_type='mess').first()
        
        # Create bank details table
        table_data = [
            ['Name of the Bank', establishment_account.bank_name if establishment_account else 'State Bank of India, Vadavalli Branch'],
            ['IFSC Code', establishment_account.ifsc_code if establishment_account else 'SBIN0005740'],
            ['Account Name & No', f"{establishment_account.account_name}    {establishment_account.account_number}" if establishment_account else 'The Warden AURCCBE Hostel Account Establishment    44281575458'],
            ['Account Name & No', f"{mess_account.account_name}    {mess_account.account_number}" if mess_account else 'The Warden AURCCBE Hostel Account Mess    44281601967']
        ]
        
        table = Table(table_data, colWidths=[2 * inch, 4.5 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F0FE')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        table.wrapOn(c, self.width, self.height)
        table.drawOn(c, 1 * inch, y_position - table._height)
        
        # Note about transfer
        y_position = y_position - table._height - 0.25 * inch
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(1 * inch, y_position, "Note: Amount to be transferred through NEFT/RTGS/Bank transfer to the respective Account.")
        
        return y_position

    def draw_qr_and_signature(self, c, start_y):
        """Draw QR code and signature section."""
        qr_image = self.generate_qr_code()
        
        # Draw QR code (left bottom)
        qr_size = 1.2 * inch
        c.drawImage(qr_image, 1 * inch, 1.5 * inch, width=qr_size, height=qr_size, mask='auto')
        
        # QR verification text
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0, 0, 0.6)
        c.drawString(1 * inch, 1.35 * inch, "Scan QR Code to verify authenticity.")
        c.setFont("Helvetica", 6)
        c.drawString(1 * inch, 1.2 * inch, f"Unique ID: {self.request.verification_code[:32]}")
        c.setFillColorRGB(0, 0, 0)
        
        # Signature (right bottom)
        warden = None
        if self.student.hostel:
            warden = self.student.hostel.wardens.first()
        
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(self.width - 1 * inch, 2.5 * inch, warden.name if warden else "DR. M. YUVARAJU, PH.D.")
        c.setFont("Helvetica", 9)
        c.drawRightString(self.width - 1 * inch, 2.3 * inch, warden.designation.upper() if warden else "DEPUTY WARDEN")

    def draw_footer(self, c):
        """Draw footer with university address."""
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(self.width / 2, 0.7 * inch, "Maruthmalai Main Road, Navayanapura, Coimbatore – 641 046")
        c.drawCentredString(self.width / 2, 0.5 * inch, "Email: aurccbe-hoste@annauniv.edu")

    def generate_pdf(self):
        """Generate the complete certificate PDF."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        # Draw all sections
        self.draw_header(c)
        self.draw_contact_details(c)
        self.draw_certificate_number_and_date(c)
        self.draw_title(c)
        content_end_y = self.draw_main_content(c)
        fee_table_end_y = self.draw_fee_table(c, content_end_y)
        bank_end_y = self.draw_bank_details(c, fee_table_end_y)
        self.draw_qr_and_signature(c, bank_end_y)
        self.draw_footer(c)

        # Add digital signature hash (very bottom)
        signature_data = f"{self.request.certificate_number}{self.student.register_number}"
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()
        c.setFont("Courier", 5)
        c.setFillColorRGB(0.8, 0.8, 0.8)
        c.drawString(50, 20, f"Digital Signature: {signature_hash[:80]}")

        c.showPage()
        c.save()

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
