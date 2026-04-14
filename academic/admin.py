from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Subject, Mark

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'school')
    search_fields = ('name', 'code')

# academic/admin.py
from django.contrib import admin
from .models import Mark, SubjectAssignment

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib import admin
# Import the models from your models.py file
from .models import Mark, SubjectAssignment

@admin.register(SubjectAssignment)
class SubjectAssignmentAdmin(admin.ModelAdmin):
    # This is the ADMIN class, not a models.Model class
    list_display = ('teacher', 'subject', 'classroom', 'year')
    list_filter = ('classroom', 'subject', 'year')
    search_fields = ('teacher__user__last_name', 'subject__name')

@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'classroom', 'total_score', 'grade', 'entered_by')
    list_filter = ('classroom', 'term', 'year')
    readonly_fields = ('updated_at',)
    
    def save_model(self, request, obj, form, change):
        # Automatically set the 'entered_by' field to the current logged-in user
        if not obj.pk: 
            obj.entered_by = request.user
        super().save_model(request, obj, form, change)
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Teacher

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('display_photo', 'full_name', 'school', 'staff_id', 'phone', 'assigned_classes')
    list_filter = ('school', 'classrooms', 'subjects')
    search_fields = ('user__first_name', 'user__last_name', 'staff_id', 'school__name')
    
    fieldsets = (
        ('Personal Identity', {
            'fields': ('user', 'school', 'staff_id', 'profile_photo', 'phone')
        }),
        ('Academic Responsibility', {
            'fields': ('classrooms', 'subjects'),
        }),
    )

    def full_name(self, obj):
        """Returns the full name with safety checks for missing users."""
        # 1. Try Teacher model fields if they exist
        first = getattr(obj, 'first_name', None)
        last = getattr(obj, 'last_name', None)
        if first or last:
            return f"{first or ''} {last or ''}".strip()
        
        # 2. Safe check: Does the user relationship exist?
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
            
        # 3. Last resort fallback
        return f"Teacher ({obj.staff_id or 'ID Missing'})"
    full_name.short_description = 'Full Name'

    def display_photo(self, obj):
        """Renders the profile photo or a placeholder."""
        if obj.profile_photo:
            # We use format_html with args to prevent the previous TypeError
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />', 
                obj.profile_photo.url
            )
        
        # Static HTML string for placeholder
        return mark_safe(
            '<div style="width: 40px; height: 40px; border-radius: 50%; background: #eee; '
            'display: flex; align-items: center; justify-content: center; font-size: 10px; '
            'color: #999; border: 1px solid #ddd;">No Photo</div>'
        )
    display_photo.short_description = 'Photo'

    def assigned_classes(self, obj):
        """Lists classrooms as a comma-separated string."""
        classes = obj.classrooms.all()
        if classes:
            return ", ".join([c.name for c in classes])
        return "Not Assigned"
    assigned_classes.short_description = 'Classes'

    
from django.contrib import admin
from .models import ClassRequirement

@admin.register(ClassRequirement)
class ClassRequirementAdmin(admin.ModelAdmin):
    # Columns to show in the list view
    list_display = ('classroom', 'term', 'year', 'school')
    
    # Sidebar filters for quick navigation
    list_filter = ('year', 'term', 'school', 'classroom')
    
    # Search box for classroom names
    search_fields = ('classroom__name', 'items')
    
    # Organizing the form layout
    fieldsets = (
        ('Context', {
            'fields': ('school', 'classroom')
        }),
        ('Timing', {
            'fields': ('term', 'year')
        }),
        ('Details', {
            'fields': ('items',),
            'description': 'Enter the requirements for the upcoming term.'
        }),
    )

    def save_model(self, request, obj, form, change):
        # Automatically assign the school from the user's session if needed
        if not obj.school_id and hasattr(request, 'school'):
            obj.school = request.school
        super().save_model(request, obj, form, change)
