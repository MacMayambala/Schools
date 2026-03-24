from .models import Invoice, FeeStructure
from students.models import Student

def generate_bulk_invoices(school, classroom, term, year):
    """
    Calculates total fees for a class based on FeeStructure 
    and creates Invoices for all students in that class.
    """
    # 1. Get all fee requirements for this class/term
    structures = FeeStructure.objects.filter(
        school=school,
        classroom=classroom,
        term=term,
        year=year
    )
    
    if not structures.exists():
        return 0, "No Fee Structure found for this class/term."

    total_bill = sum(item.amount for item in structures)
    students = Student.objects.filter(school=school, classroom=classroom, is_active=True)
    
    count = 0
    for student in students:
        # Avoid double-billing if an invoice already exists
        invoice, created = Invoice.objects.get_or_create(
            school=school,
            student=student,
            term=term,
            year=year,
            defaults={'total_amount': total_bill}
        )
        if created:
            count += 1
            
    return count, f"Successfully generated {count} invoices for {classroom.name}."