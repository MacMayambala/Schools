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



# Add these at the bottom of core/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .models import CustomUser, Role, AuditLog
from .forms import UserCreationForm
from .utils import log_activity


@login_required
def user_list(request):
    status_filter = request.GET.get('status', 'all')

    users = CustomUser.objects.filter(school=request.school).select_related('user', 'role')

    if status_filter == 'active':
        users = users.filter(user__is_active=True)
    elif status_filter == 'locked':
        users = users.filter(user__is_active=False)

    users = users.order_by('-date_joined')

    context = {
        'users': users,
        'current_filter': status_filter,
    }
    return render(request, 'core/user_list.html', context)



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import UserCreationForm
from .models import CustomUser
from .utils import log_activity

@login_required
def user_create(request):
    # Safe Permission Check
    try:
        custom_user = request.user.customuser
        if not custom_user.role or not custom_user.role.can_manage_users:
            messages.error(request, "You do not have permission to manage users.")
            return redirect('core:user_list')
    except CustomUser.DoesNotExist:
        messages.error(request, "Your account is not properly configured. Contact Administrator.")
        return redirect('core:index')

    if request.method == 'POST':
        form = UserCreationForm(request.POST, school=request.school)
        if form.is_valid():
            username = form.cleaned_data['username']
            
            # Check for existing username (UserCreationForm may handle this, 
            # but explicit check is safer if using a custom base User model)
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
            else:
                # Create the base Django User
                user = User.objects.create_user(
                    username=username,
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                )
                
                # Create the linked CustomUser (Tenant-aware)
                CustomUser.objects.create(
                    user=user,
                    school=request.school,
                    role=form.cleaned_data['role'],
                    is_active=True
                )
                
                # Log the activity
                log_activity(
                    request, 
                    action="User Created", 
                    resource="User", 
                    object_id=user.id,
                    details={
                        "username": username, 
                        "role": form.cleaned_data['role'].name
                    }
                )
                
                messages.success(request, f"User '{username}' created successfully!")
                return redirect('core:user_list')
    else:
        form = UserCreationForm(school=request.school)

    return render(request, 'core/user_form.html', {'form': form})

from django.contrib.auth.models import Group
@login_required
def user_edit(request, pk):
    # 1. Fetch the CustomUser profile
    custom_user = get_object_or_404(CustomUser, pk=pk, school=request.school)
    # 2. Get the actual Django User object attached to that profile
    auth_user = custom_user.user 

    if request.method == 'POST':
        # Fetch the selected group (ensure it belongs to the school if you've extended Group)
        group_id = request.POST.get('role')
        new_group = get_object_or_404(Group, id=group_id)

        # Update auth_user groups
        # .set() replaces all existing groups with the new one
        auth_user.groups.set([new_group])
        
        # Update CustomUser fields
        custom_user.is_active = bool(request.POST.get('is_active'))
        custom_user.phone = request.POST.get('phone', '')
        custom_user.position = request.POST.get('position', '')
        custom_user.save()

        # Update the auth_user's active status as well
        auth_user.is_active = custom_user.is_active
        auth_user.save()

        # Activity Logging
        from .utils import log_activity
        log_activity(
            request, 
            action="User Updated", 
            resource="User", 
            object_id=auth_user.id,
            details={"username": auth_user.username, "role": new_group.name}
        )
        
        messages.success(request, f"Permissions updated for {auth_user.username}")
        return redirect('core:user_list')

    # Fetch groups for the dropdown
    # Note: If your Groups aren't school-specific, remove the school filter
    groups = Group.objects.all() 
    
    context = {
        'custom_user': custom_user, 
        'groups': groups
    }
    return render(request, 'core/user_edit.html', context)


# Add this function to core/views.py

@login_required
def unlock_user(request, pk):
    """Unblock a user who was locked due to too many failed attempts"""
    if not request.user.customuser.role or not request.user.customuser.role.can_manage_users:
        messages.error(request, "You don't have permission to unlock users.")
        return redirect('core:user_list')

    custom_user = get_object_or_404(CustomUser, pk=pk, school=request.school)
    user = custom_user.user

    if request.method == 'POST':
        user.is_active = True
        custom_user.failed_login_attempts = 0
        user.save()
        custom_user.save()

        from .utils import log_activity
        log_activity(request, "User Unlocked", "User", user.id, 
                    {"username": user.username, "unlocked_by": request.user.username})

        messages.success(request, f"User '{user.username}' has been successfully unlocked.")
        return redirect('core:user_list')

    # GET request - Show confirmation
    context = {
        'custom_user': custom_user,
        'user': user
    }
    return render(request, 'core/user_unlock_confirm.html', context)

@login_required
def user_delete(request, pk):
    custom_user = get_object_or_404(CustomUser, pk=pk, school=request.school)
    
    # Prevent deleting yourself or last admin
    if custom_user.user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('core:user_list')
    
    if request.method == 'POST':
        username = custom_user.user.username
        custom_user.user.delete()
        
        from .utils import log_activity
        log_activity(request, "User Deleted", "User", None, {"username": username})
        
        messages.success(request, f"User {username} has been permanently deleted.")
        return redirect('core:user_list')
    
    return render(request, 'core/user_confirm_delete.html', {'custom_user': custom_user})


@login_required
def audit_logs(request):
    logs = AuditLog.objects.filter(school=request.school).select_related('user')[:300]
    return render(request, 'core/audit_logs.html', {'logs': logs})




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User, Permission
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

@user_passes_test(lambda u: u.is_superuser)
def assign_rights(request):
    # Fetch all staff users (excluding superusers if you want to protect them)
    staff_users = User.objects.exclude(is_superuser=True).order_by('-date_joined')
    
    # Optional: Group permissions by module (content_type) for the modal
    # In a real app, you might want to filter specific app permissions like 'finance' or 'students'
    all_permissions = Permission.objects.select_related('content_type').all()

    context = {
        'staff_users': staff_users,
        # In a real scenario, you'd group these in a dictionary for the template loop
        'permissions': all_permissions, 
    }
    return render(request, 'core/assign_rights.html', context)

@user_passes_test(lambda u: u.is_superuser)
def update_user_rights(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        
        # 1. Update Staff Status
        is_staff = request.POST.get('is_staff') == 'on'
        target_user.is_staff = is_staff
        
        # 2. Update Individual Permissions
        # Get list of permission IDs from the checkboxes
        perm_ids = request.POST.getlist('perms')
        
        # Clear existing permissions and set new ones
        target_user.user_permissions.set(perm_ids)
        target_user.save()
        
        messages.success(request, f"Permissions for {target_user.username} updated successfully.")
        return redirect('core:assign_rights')

    return redirect('core:assign_rights')




from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

@user_passes_test(lambda u: u.is_superuser)
def group_list(request):
    groups = Group.objects.all().prefetch_related('permissions', 'user_set')
    return render(request, 'core/group_list.html', {'groups': groups})

@user_passes_test(lambda u: u.is_superuser)
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('group_name')
        group, created = Group.objects.get_or_create(name=name)
        return redirect('core:edit_group', group_id=group.id)
    return redirect('core:group_list')

@user_passes_test(lambda u: u.is_superuser)
def edit_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    if request.method == 'POST':
        perm_ids = request.POST.getlist('permissions')
        group.permissions.set(perm_ids)
        messages.success(request, f"Permissions for '{group.name}' updated.")
        return redirect('core:group_list')

    # Group permissions by app for easier selection
    all_perms = Permission.objects.select_related('content_type').order_by('content_type__app_label')
    
    context = {
        'group': group,
        'all_perms': all_perms,
    }
    return render(request, 'core/edit_group.html', context)