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