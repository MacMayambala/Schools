from django.db import models

# Create your models here.
from django.db import models
from core.models import TenantModel

class Classroom(TenantModel):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=10, help_text="e.g., P1")
    # Add this to handle sorting and promotion logic
    level = models.PositiveIntegerField(default=1, help_text="Order of class (1 for P1, 2 for P2, etc.)")

    class Meta:
        ordering = ['level'] # This makes dropdowns and lists look organized
        unique_together = ('school', 'level') # Optional: prevents duplicate levels in one school

    def __str__(self):
        return f"{self.name} ({self.school.code})"
    
    
# students/models.py
from django.db import models
from core.models import TenantModel
import datetime

import datetime
from django.db import models
from core.models import TenantModel

class Classroom(TenantModel):
    """ e.g., Primary One, Senior One """
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=10, help_text="e.g., P1")

    def __str__(self):
        return f"{self.name} ({self.school.code})"


class Student(TenantModel):
    # --- Student Basic Info ---
    photo = models.ImageField(
        upload_to='students/photos/', 
        null=True, 
        blank=True,
        help_text="Upload a passport-sized photo"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    admission_number = models.CharField(max_length=50, unique=True, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='students')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], null=True)
    
    # --- Guardian Details (Captured at Registration) ---
    guardian_name = models.CharField(max_length=200, verbose_name="Parent/Guardian Name")
    guardian_phone = models.CharField(max_length=20, verbose_name="Guardian Phone Number")
    guardian_email = models.EmailField(blank=True, null=True)
    guardian_relation = models.CharField(
        max_length=50,
        choices=[
            ('FATHER', 'Father'),
            ('MOTHER', 'Mother'),
            ('GUARDIAN', 'Legal Guardian'),
            ('RELATIVE', 'Relative'),
            ('OTHER', 'Other'),
        ],
        default='FATHER'
    )
    guardian_address = models.TextField(blank=True, null=True)

    # --- System Info ---
    date_enrolled = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.admission_number:
            year = datetime.date.today().year
            # Get count for the current school tenant
            count = Student.objects.filter(school=self.school).count() + 1
            # Generates: SAO/2026/001
            self.admission_number = f"{self.school.code}/{year}/{count:03d}"
        super().save(*args, **kwargs)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.admission_number} - {self.get_full_name()}"