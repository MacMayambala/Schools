from django.db import models

# Create your models here.
from django.db import models
from core.models import School
from django.conf import settings

class ReportLog(models.Model):
    REPORT_TYPES = [
        ('FINANCE', 'Financial Report'),
        ('ACADEMIC', 'Academic Report'),
        ('STUDENT', 'Student Population'),
    ]
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report_type} - {self.created_at.date()}"