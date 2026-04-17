from django.db import models
from core.models import School
from students.models import Student, Classroom

class Subject(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True)
    # This links subjects to specific classes (e.g., Physics for S.4)
    classrooms = models.ManyToManyField(Classroom, related_name="subjects")

    def __str__(self):
        return f"{self.name} ({self.school.code})"

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class SubjectAssignment(models.Model):
    # Change 'School' to 'school.School' if the app name is 'school'
    school = models.ForeignKey('core.School', on_delete=models.CASCADE)
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='assignments')
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    classroom = models.ForeignKey('students.Classroom', on_delete=models.CASCADE)
    year = models.IntegerField(default=2026)

    class Meta:
        unique_together = ('subject', 'classroom', 'year')

    def __str__(self):
        return f"{self.teacher.user.last_name} - {self.subject.name} ({self.classroom.name})"


from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Mark(models.Model):
    school = models.ForeignKey('core.School', on_delete=models.CASCADE)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    classroom = models.ForeignKey('students.Classroom', on_delete=models.CASCADE)
    
    term = models.CharField(max_length=20) 
    year = models.IntegerField(default=2026)
    
    mid_term_mark = models.FloatField(null=True, blank=True)
    end_term_mark = models.FloatField(null=True, blank=True)
    
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_score(self):
        return (self.mid_term_mark or 0) + (self.end_term_mark or 0)

    @property
    def grade(self):
        score = self.total_score
        if score >= 80: return 'D1'
        if score >= 75: return 'D2'
        if score >= 70: return 'C3'
        if score >= 65: return 'C4'
        if score >= 60: return 'C5'
        if score >= 55: return 'C6'
        if score >= 50: return 'P7'
        if score >= 45: return 'P8'
        return 'F9'

    @property
    def grade_remark(self):
        remarks = {
            'D1':'Excellent','D2':'Very Good','C3':'Good',
            'C4':'Quite Good','C5':'Satisfactory','C6':'Fair',
            'P7':'Pass','P8':'Weak Pass','F9':'Fail'
        }
        return remarks.get(self.grade, 'N/A')

    def clean(self):
        # 1. If no user is assigned, skip validation
        if not self.entered_by:
            return

        # 2. Bypass validation for Superusers (Admins)
        if self.entered_by.is_superuser:
            return

        # 3. Validation for Teachers
        try:
            # Using getattr to safely check for teacher_profile
            teacher_profile = getattr(self.entered_by, 'teacher_profile', None)
            
            if not teacher_profile:
                raise ValidationError("Access Denied: Your account is not linked to a Teacher Profile.")

            from .models import SubjectAssignment
            assigned = SubjectAssignment.objects.filter(
                teacher=teacher_profile,
                subject=self.subject,
                classroom=self.classroom,
                year=self.year
            ).exists()
            
            if not assigned:
                raise ValidationError(
                    f"Access Denied: You do not teach {self.subject.name} in {self.classroom.name}."
                )
        except Exception as e:
            if isinstance(e, ValidationError):
                raise e
            raise ValidationError(f"Security validation failed: {str(e)}")

    def save(self, *args, **kwargs):
        # We call full_clean so that the clean() method above is executed
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        # Fixed: Safe way to get student name since 'user' might not exist on student
        student_name = getattr(self.student, 'full_name', str(self.student))
        return f"{student_name} - {self.subject.name}: {self.total_score}"


####################################################################################################################################
from django.db import models
from django.conf import settings
# Assuming you use a TenantModel for multi-school support
import os
from django.db import models
from django.conf import settings

class Teacher(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='teachers')
    # Link is now optional (null=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        related_name='teacher_profile', 
        null=True, 
        blank=True
    )
    # Fields to store names if no user exists
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    staff_id = models.CharField(max_length=20, unique=True)
    profile_photo = models.ImageField(upload_to='teachers/photos/', null=True, blank=True)
    phone = models.CharField(max_length=15)
    
    subjects = models.ManyToManyField('academic.Subject', related_name='teachers', blank=True)
    classrooms = models.ManyToManyField('students.Classroom', related_name='teachers', blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

class ClassRequirement(models.Model):
    school = models.ForeignKey('core.School', on_delete=models.CASCADE)
    classroom = models.ForeignKey('students.Classroom', on_delete=models.CASCADE)
    term = models.CharField(max_length=20) 
    year = models.IntegerField()
    # Change help_status to help_text below:
    items = models.TextField(help_text="List items separated by commas or new lines")

    def __str__(self):
        return f"Requirements for {self.classroom.name} - Term {self.term}"
