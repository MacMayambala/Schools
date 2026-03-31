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