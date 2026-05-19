# core/utils.py
from .models import AuditLog

# core/utils.py
from .models import AuditLog


def log_activity(request, action, resource=None, object_id=None, details=None):
    """
    Recommended Audit Logging Function
    """
    if details is None:
        details = {}

    # Better IP handling (supports reverse proxies like Nginx, Cloudflare, etc.)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    AuditLog.objects.create(
        school=request.school,
        user=request.user if request.user.is_authenticated else None,
        action=action,
        model_name=resource,           # e.g. "Student", "Invoice", "Payment"
        object_id=object_id,
        details=details,
        ip_address=ip
    )