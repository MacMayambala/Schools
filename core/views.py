from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from students.models import Student
from finance.models import Invoice
import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum
import json

from students.models import Student
from finance.models import Invoice
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum

from students.models import Student
from finance.models import Invoice


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum

from students.models import Student
from finance.models import Invoice

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.utils import timezone
from decimal import Decimal
from finance.models import Invoice
from students.models import Student

@login_required
def index(request):
    school = request.school
    
    # --- 1. Basic KPI Stats ---
    student_count = Student.objects.filter(school=school, is_active=True).count()
    
    finance_stats = Invoice.objects.filter(school=school).aggregate(
        total_expected=Sum('total_amount'),
        total_paid=Sum('paid_amount')
    )
    
    expected = finance_stats['total_expected'] or Decimal('0.00')
    paid = finance_stats['total_paid'] or Decimal('0.00')
    balance = expected - paid

    # --- 2. Pie Chart Logic (Manual Loop for Accuracy) ---
    students = Student.objects.filter(school=school, is_active=True).prefetch_related('invoices')

    cleared_students = 0
    arrears_students = 0

    for student in students:
        # Use the prefetch to avoid hitting the DB inside the loop
        invoices = student.invoices.all()
        
        # Ensure we treat None as 0
        total_billed = sum((inv.total_amount or Decimal('0.00')) for inv in invoices)
        total_paid = sum((inv.paid_amount or Decimal('0.00')) for inv in invoices)

        # Logic: Only count students who have actually been billed
        if total_billed > 0:
            if (total_billed - total_paid) <= 0:
                cleared_students += 1
            else:
                arrears_students += 1

    # --- 3. SQLite-Safe Revenue Logic ---
    # Instead of TruncMonth (which crashes SQLite often), we'll do a simple monthly sum for the current year
    labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    revenue_data = []
    
    current_year = timezone.now().year
    
    for month_index in range(1, 13):
        monthly_sum = Invoice.objects.filter(
            school=school,
            created_at__year=current_year,
            created_at__month=month_index
        ).aggregate(total=Sum('paid_amount'))['total'] or 0
        
        revenue_data.append(float(monthly_sum))

    # --- 4. Context Assembly ---
    context = {
        'student_count': student_count,
        'total_fees': paid,
        'balance': balance,
        'status_data': [cleared_students, arrears_students],
        'revenue_data': revenue_data,
        'labels': labels,
        'recent_invoices': Invoice.objects.filter(school=school)
            .select_related('student')
            .order_by('-created_at')[:5]
    }
    
    return render(request, 'core/index.html', context)

from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages

# academic/views.py

from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import logout

from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect

from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.contrib.auth import logout, authenticate
from django.shortcuts import redirect
from django.contrib.auth.models import User


from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.contrib.auth import logout, authenticate
from django.shortcuts import redirect
from django.contrib.auth.models import User

class SchoolLoginView(SuccessMessageMixin, LoginView):
    template_name = 'registration/login.html'
    success_message = "Welcome back! ✨ Great to see you again. Let's have a productive session! 🚀"

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        try:
            user_obj = User.objects.get(username=username)
            # Check if account is already locked before proceeding
            if not user_obj.is_active:
                messages.error(self.request, "Account Locked! 🔒 Contact Admin to reactivate.")
                return redirect('login')
            
            # Reset failed attempts on success
            if hasattr(user_obj, 'customuser'):
                user_obj.customuser.failed_login_attempts = 0
                user_obj.customuser.save()
        except User.DoesNotExist:
            pass

        return super().form_valid(form)

    def form_invalid(self, form):
        # 1. Kill the long default Django message
        form.errors.clear() 

        # 2. Logic for failed attempts (The 3-Strike Rule)
        username = self.request.POST.get('username')
        try:
            user_obj = User.objects.get(username=username)
            custom_user = getattr(user_obj, 'customuser', None)
            
            if custom_user:
                custom_user.failed_login_attempts += 1
                custom_user.save()
                
                if custom_user.failed_login_attempts >= 3:
                    user_obj.is_active = False # Deactivate the account
                    user_obj.save()
                    messages.error(self.request, "Too many attempts! 🛡️ Account deactivated for security.")
                else:
                    messages.error(self.request, "Oops! 🔑 Invalid Staff ID or Password.")
            else:
                messages.error(self.request, "Oops! 🔑 Invalid Staff ID or Password.")
        except User.DoesNotExist:
            messages.error(self.request, "Oops! 🔑 Invalid Staff ID or Password.")

        # 3. Redirect back to login to trigger the 10-second JavaScript timer
        return redirect('core:login')

def logout_view(request):
    """Handles vibey logout and session cleanup"""
    logout(request)
    request.session.flush() 
    messages.info(request, "See you soon! 👋 You have been safely logged out. 🌟")
    return redirect('core:login')


def custom_404(request, exception=None): # Use =None to be safe
    return render(request, '404.html', status=404)



from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

import logging
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.models import User

# Set up logging to track password reset attempts
logger = logging.getLogger(__name__)

# 1. Submission View: Enhanced with User Feedback & Logging
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.models import User
from django import forms

from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

class MyPasswordResetView(auth_views.PasswordResetView):
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/password_reset_email.html' # This is used for plain text fallback
    html_email_template_name = 'auth/password_reset_email.html' # THIS makes it look "proper"
    subject_template_name = 'auth/password_reset_subject.txt'
    success_url = reverse_lazy('core:password_reset_done')

    
    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        # Check for active user with case-insensitive email
        user_exists = User.objects.filter(email__iexact=email, is_active=True).exists()
        
        if not user_exists:
            # Add error specifically to the email field
            form.add_error('email', "This email address is not registered in our system.")
            logger.warning(f"Password reset failed: {email} not found.")
            return self.form_invalid(form)
        
        logger.info(f"Password reset link sent to: {email}")
        return super().form_valid(form)

class MyPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'auth/password_reset_done.html'

class MyPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('core:password_reset_complete')

class MyPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'auth/password_reset_complete.html'




import json
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from finance.models import Invoice, Payment, FeeStructure

# def dashboard_view(request):
#     # 1. Use 'created_at' to match your Model definition
#     # 2. Filter by 'request.school' to ensure multi-tenant security
#     monthly_revenue = Invoice.objects.filter(
#         school=request.school, 
#         created_at__year=2026
#     ).annotate(
#         month=TruncMonth('created_at')
#     ).values('month').annotate(
#         total=Sum('paid_amount') # Use 'paid_amount' from your model
#     ).order_by('month')

#     # Format data for JavaScript (ApexCharts)
#     labels = [item['month'].strftime("%b") for item in monthly_revenue]
#     # Ensure we handle None values if a month has no payments
#     data = [float(item['total'] or 0) for item in monthly_revenue]

#     context = {
#         'labels': json.dumps(labels),
#         'revenue_data': json.dumps(data),
#         # Adding some extra KPIs for a more professional dashboard
#         'total_revenue': sum(data),
#         'student_count': request.school.student_set.count() if hasattr(request.school, 'student_set') else 0,
#     }
    
#     return render(request, 'core/index.html', context)


import json
from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal
from finance.models import Invoice
from students.models import Student

import json
from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from finance.models import Invoice
from students.models import Student

@login_required
def dashboard_view(request):
    school = request.school 

    # --- 1. KPI Metrics ---
    student_count = Student.objects.filter(school=school).count()
    
    finance_stats = Invoice.objects.filter(school=school).aggregate(
        total_expected=Sum('total_amount'),
        total_paid=Sum('paid_amount')
    )
    
    expected = finance_stats['total_expected'] or Decimal('0.00')
    paid = finance_stats['total_paid'] or Decimal('0.00')
    balance = expected - paid

    # --- 2. Graphical Data (Monthly Revenue Trend) ---
    # We fetch ALL invoices for the year and group them in Python to avoid SQLite date errors
    labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    chart_data = [0.0] * 12 # Initialize 12 months with 0.0
    
    current_year = 2026
    
    # Fetch all relevant invoices once
    yearly_invoices = Invoice.objects.filter(
        school=school,
        created_at__year=current_year
    ).values('created_at', 'paid_amount')

    for inv in yearly_invoices:
        if inv['created_at']:
            # index 0 = Jan, index 1 = Feb, etc.
            month_idx = inv['created_at'].month - 1 
            chart_data[month_idx] += float(inv['paid_amount'] or 0)

    # --- 3. Recent Activity ---
    recent_invoices = Invoice.objects.filter(school=school).select_related('student').order_by('-id')[:5]

    context = {
        'student_count': student_count,
        'total_fees': paid,
        'balance': balance,
        'labels': json.dumps(labels),
        'revenue_data': json.dumps(chart_data),
        'recent_invoices': recent_invoices,
    }
    
    return render(request, 'core/index.html', context)