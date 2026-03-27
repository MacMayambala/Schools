from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from students.models import Student
from finance.models import Invoice

@login_required
def index(request):
    """
    The Main Dashboard view for Saozirobwe.
    Calculates key metrics based on the current user's school.
    """
    school = request.school # Handled by your SchoolMiddleware
    
    # 1. Total Students Count
    student_count = Student.objects.filter(school=school).count()
    
    # 2. Finance Metrics
    # We get the sum of total_amount and paid_amount for all invoices in this school
    finance_stats = Invoice.objects.filter(school=school).aggregate(
        total_expected=Sum('total_amount'),
        total_paid=Sum('paid_amount')
    )
    
    expected = finance_stats['total_expected'] or 0
    paid = finance_stats['total_paid'] or 0
    balance = expected - paid

    context = {
        'student_count': student_count,
        'total_fees': paid,
        'balance': balance,
        # We can also pass recent invoices for the 'Recent Activities' table
        'recent_invoices': Invoice.objects.filter(school=school).order_by('-id')[:5]
    }
    
    return render(request, 'core/index.html', context)



from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    request.session.flush() # Completely destroys the session data
    return redirect('login')