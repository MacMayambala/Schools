# core/models.py
from django.db import models
from django.contrib.auth.models import User

class School(models.Model):
    subdomain = models.CharField(max_length=100, unique=True, db_index=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True) # e.g. SAO-01
    admin = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Professional Details for the Report Header
    motto = models.CharField(max_length=255, blank=True, null=True, help_text="School Motto")
    address = models.TextField(blank=True, null=True, help_text="Physical/Postal Address")
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    logo = models.ImageField(
        upload_to='school/logos/', 
        null=True, 
        blank=True,
        help_text="Official school badge/logo"
    )

    def __str__(self):
        return f"{self.name} ({self.code})"
    


class TenantModel(models.Model):
    """ Abstract model so everything inherits 'school' automatically """
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True




# core/models.py
from django.db import models
from django.contrib.auth.models import User, Permission
from django.utils import timezone


class Role(models.Model):
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100, help_text="e.g. Principal, Accountant, Teacher")
    description = models.TextField(blank=True)

    # Quick Permission Flags
    can_manage_students = models.BooleanField(default=False)
    can_manage_finance = models.BooleanField(default=False)
    can_manage_staff = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=True)
    can_manage_settings = models.BooleanField(default=False)

    class Meta:
        unique_together = ('school', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.school.code})"


class CustomUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customuser')
    school = models.ForeignKey('School', on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


# core/models.py - Update AuditLog
class AuditLog(models.Model):
    school = models.ForeignKey('School', on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    action = models.CharField(max_length=150)           # e.g. "Created Student", "Approved Payment"
    model_name = models.CharField(max_length=100, blank=True)   # "Student", "Invoice"
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return f"{self.timestamp} | {self.user} | {self.action}"