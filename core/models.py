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
