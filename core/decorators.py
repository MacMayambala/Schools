from django.core.exceptions import PermissionDenied
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

def permission_required(permission_field):
    """
    Decorator to check if user has a specific permission field in their role.
    Usage: @permission_required('can_manage_users')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                role = request.user.customuser.role
                if role and getattr(role, permission_field, False):
                    return view_func(request, *args, **kwargs)
            except (AttributeError, Exception):
                pass
            
            messages.error(request, "You do not have permission to perform this action.")
            return redirect('core:user_list')
        return _wrapped_view
    return decorator