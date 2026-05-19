# core/context_processors.py
from .models import School

# core/context_processors.py
from core.models import School

# core/context_processors.py
def school_context(request):
    if not request.user.is_authenticated:
        return {'school': None}

    school = None
    # Check if Admin
    from core.models import School
    try:
        school = School.objects.get(admin=request.user)
    except School.DoesNotExist:
        # Check if Teacher
        profile = getattr(request.user, 'teacher_profile', None)
        if profile:
            school = profile.school

    # This makes request.school available in all views
    request.school = school 
    return {'school': school}