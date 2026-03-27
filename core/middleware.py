from .models import School

class SchoolMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Get the host (e.g., 'sao.localhost' or 'saozirobwe.yoursystem.com')
        host = request.get_host().split(':')[0]
        host_parts = host.split('.')

        # 2. Determine if we have a subdomain
        # On Localhost: ['sao', 'localhost'] -> length 2
        # On Production: ['saozirobwe', 'yoursystem', 'com'] -> length 3
        subdomain = None
        
        if len(host_parts) >= 2:
            # We assume the first part is always the subdomain
            subdomain = host_parts[0]
            
            # Filter the school by the 'subdomain' field we added to the model
            request.school = School.objects.filter(subdomain__iexact=subdomain).first()
        else:
            request.school = None

        # 3. Fallback: If no subdomain found, check if a logged-in user is an admin for a school
        if not request.school and request.user.is_authenticated:
            # This links the logged-in staff member back to their specific institution
            request.school = School.objects.filter(admin=request.user).first()

        # 4. Final Fallback: If still nothing, you can set a 'Default' school for dev purposes
        # request.school = request.school or School.objects.first()

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
        exempt_url_names = ['login', 'register', 'password_reset', 'home']

        # 3. Check authentication logic
        if not request.user.is_authenticated:
            if url_name not in exempt_url_names and not request.path.startswith(settings.STATIC_URL):
                # Redirect to login, and keep the 'next' path so they return where they were
                login_url = reverse('login')
                return redirect(f"{login_url}?next={request.path}")

        return self.get_response(request)