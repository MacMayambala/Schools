# core/context_processors.py
from .models import School

def school_context(request):
    if request.user.is_authenticated:
        try:
            # Change admin_user to admin here too
            school = School.objects.get(admin=request.user)
            return {'school': school}
        except School.DoesNotExist:
            return {'school': None}
    return {'school': None}