from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from students.models import Student
from finance.models import Invoice
from academic.models import Teacher

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from students.models import Student
# ... other imports (Invoice, Teacher, etc.)

@login_required
def report_hub(request):
    school = request.school
    
    # 1. Enrollment Statistics (Filtered by Tenant School)
    # We filter by is_active=True to ensure we aren't counting withdrawn students
    active_students = Student.objects.filter(school=school, is_active=True)
    
    total_students = active_students.count()
    
    # Get counts based on your model choices [('M', 'Male'), ('F', 'Female')]
    male_count = active_students.filter(gender='M').count()
    female_count = active_students.filter(gender='F').count()

    # 2. Section Distribution (Day vs Boarding)
    day_scholars = active_students.filter(section='Day').count()
    boarders = active_students.filter(section='Boarding').count()

    # ... keep your existing Financial/Teacher logic here ...

    context = {
        'total_students': total_students,
        'male_count': male_count,
        'female_count': female_count,
        'day_scholars': day_scholars,
        'boarders': boarders,
        # ... other context variables ...
    }
    return render(request, 'reports/hub.html', context)