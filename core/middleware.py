from .models import School

class SchoolMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Extract Subdomain
        host = request.get_host().split(':')[0]
        host_parts = host.split('.')
        subdomain = host_parts[0] if len(host_parts) >= 2 else None

        # 2. Identify School by Subdomain
        request.school = None
        if subdomain and subdomain.lower() not in ['www', '127', 'localhost']:
            request.school = School.objects.filter(subdomain__iexact=subdomain).first()

        # 3. CRITICAL FIX: Identify School by User Session
        # If subdomain lookup fails, use the User's linked school.
        # This ensures that even on 127.0.0.1, the financial views work.
        if not request.school and request.user.is_authenticated:
            # Check if your User model has a 'school' FK, or use the 'admin' lookup
            request.school = getattr(request.user, 'school', None) or \
                             School.objects.filter(admin=request.user).first()

        # 4. Final Security Check
        # If we are in a finance view but request.school is still None, 
        # the system won't know which data to pull.
        
        response = self.get_response(request)
        return response
    

from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.conf import settings

class GlobalLoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Get the name of the current view's URL pattern
        url_name = resolve(request.path_info).url_name

        # 2. Define URLs that MUST be accessible without logging in
        # Add your password reset or landing page names here
        exempt_url_names = ['login', 'register', 'password_reset', 'password_reset_done', 'password_reset_confirm', 'password_reset_complete']

        # 3. Check authentication logic
        if not request.user.is_authenticated:
            if url_name not in exempt_url_names and not request.path.startswith(settings.STATIC_URL):
                # Redirect to login, and keep the 'next' path so they return where they were
                login_url = reverse('core:login')
                return redirect(f"{login_url}?next={request.path}")

        return self.get_response(request)
    


# core/middleware.py (Example)
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check Admin first
            school = getattr(request.user, 'managed_school', None) # If you have a related name
            if not school:
                # Check Teacher profile
                profile = getattr(request.user, 'teacher_profile', None)
                school = profile.school if profile else None
            
            request.school = school
        else:
            request.school = None

        return self.get_response(request)