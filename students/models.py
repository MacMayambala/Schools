from django.db import models
from core.models import TenantModel
import datetime

class Classroom(TenantModel):
    """Class Level (P1, P2, Grade 4, etc.)"""
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=10, help_text="e.g., P1")
    level = models.PositiveIntegerField(default=1, help_text="Order of class (1 for P1, 2 for P2, etc.)")

    class Meta:
        ordering = ['level']
        unique_together = ('school', 'level')

    def __str__(self):
        return self.name


class Stream(TenantModel):
    """Stream / Section (A, B, North, Blue, etc.)"""
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ['name']
        # Ensure a school doesn't have duplicate stream names (e.g., two "North" streams)
        unique_together = ('school', 'name')

    def __str__(self):
        return self.name


class ClassStream(TenantModel):
    """Actual Class + Stream junction (P4A, P4B, etc.)"""
    classroom = models.ForeignKey(
        Classroom, 
        on_delete=models.CASCADE, 
        related_name='class_streams'
    )
    stream = models.ForeignKey(
        Stream, 
        on_delete=models.CASCADE, 
        related_name='class_streams'
    )
    
    class_teacher = models.ForeignKey(
        'academic.Teacher',  # String reference to avoid circular imports
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='class_streams_taught'
    )

    capacity = models.PositiveIntegerField(default=40)
    room_number = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('school', 'classroom', 'stream')
        ordering = ['classroom__level', 'stream__name']
        verbose_name = "Class Stream"
        verbose_name_plural = "Class Streams"

    def __str__(self):
        return self.display_name

    @property
    def full_name(self):
        return f"{self.classroom.name} - {self.stream.name}"

    @property
    def display_name(self):
        return f"{self.classroom.short_name}{self.stream.name}"


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
    
    # admission_number is unique per school, but CharField unique=True is global.
    # We keep unique=True but ensure the school code prefix makes it globally unique.
    admission_number = models.CharField(max_length=50, unique=True, editable=False, db_index=True)
    studentPaymentCode = models.CharField(max_length=50, blank=True, null=True, unique=True)
    
    class_stream = models.ForeignKey(
        'ClassStream', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='students'
    )

    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10, 
        choices=[('M', 'Male'), ('F', 'Female')], 
        null=True, 
        blank=True
    )
    
    SECTION_CHOICES = [('Day', 'Day'), ('Boarding', 'Boarding')]
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default='Day')
    
    # --- Guardian Details ---
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
                # Generate Year
                year = datetime.date.today().year
                
                # 1. Use school_id directly for speed and to avoid object-lookup errors
                # 2. Use prefix with a safe fallback
                prefix = "STD"
                if self.school:
                    prefix = getattr(self.school, 'code', "STD")
                
                # 3. Explicit filter by school_id
                count = Student.objects.filter(school_id=self.school_id).count() + 1
                self.admission_number = f"{prefix}/{year}/{count:03d}"
            
            # FIX: Ensure we pass kwargs correctly and avoid potential positional confusion
            super().save(*args, **kwargs)

    # models.py
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.admission_number} - {self.get_full_name()}"