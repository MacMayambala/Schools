from django.db import transaction
from .models import Invoice, FeeStructure
from students.models import Student

def generate_bulk_invoices(school, classroom, term, year):
    """
    Professional Billing: Assigns different totals to students 
    based on their Section (Day/Boarding).
    """
    students = Student.objects.filter(
        school=school, 
        classroom=classroom, 
        is_active=True
    )
    
    # 1. Pre-fetch FeeStructures for both Day and Boarding to avoid multiple DB hits
    fee_map = {
        fs.section: fs.total_fees 
        for fs in FeeStructure.objects.filter(
            school=school, classroom=classroom, term=term, year=year
        )
    }

    if not fee_map:
        return 0, f"Error: No Fee Structures defined for {classroom.name}."

    count = 0
    with transaction.atomic(): # Ensures data integrity
        for student in students:
            # 2. Get the specific amount for THIS student's section
            # If a student is 'Boarding' but no boarding fee exists, skip or fallback
            bill_amount = fee_map.get(student.section)
            
            if bill_amount:
                invoice, created = Invoice.objects.get_or_create(
                    school=school,
                    student=student,
                    term=term,
                    year=year,
                    defaults={'total_amount': bill_amount}
                )
                if created:
                    count += 1
            
    return count, f"Generated {count} invoices for {classroom.name}."