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
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    # What columns to show in the list view
    list_display = ('display_photo', 'full_name', 'staff_id', 'phone', 'assigned_classes')
    list_filter = ('classrooms', 'subjects')
    search_fields = ('user__first_name', 'user__last_name', 'staff_id')
    
    # Organizing the "Add/Edit" page
    fieldsets = (
        ('Personal Identity', {
            'fields': ('user', 'staff_id', 'profile_photo', 'phone')
        }),
        ('Academic Responsibility', {
            'fields': ('classrooms', 'subjects'),
            'description': 'Assign the classes and subjects this teacher is responsible for.'
        }),
    )

    # Helper to show full name in list
    def full_name(self, obj):
        return obj.user.get_full_name()
    full_name.short_description = 'Teacher Name'

    # Helper to show photo thumbnail in list
    def display_photo(self, obj):
        if obj.profile_photo:
            return format_html('<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />', obj.profile_photo.url)
        return format_html('<div style="width: 40px; height: 40px; border-radius: 50%; background: #eee; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #999;">No Image</div>')
    display_photo.short_description = 'Photo'

    # Helper to list assigned classes in the table
    def assigned_classes(self, obj):
        return ", ".join([c.name for c in obj.classrooms.all()])
    assigned_classes.short_description = 'Classes'