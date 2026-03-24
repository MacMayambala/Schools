from django.contrib import admin
from .models import Student, Classroom

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'school')
    list_filter = ('school',)
    search_fields = ('name', 'short_name')

# students/admin.py
from django.contrib import admin
from .models import Student, Classroom

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'first_name', 'last_name', 'classroom', 'guardian_name', 'guardian_phone')
    list_filter = ('classroom', 'is_active')
    search_fields = ('first_name', 'last_name', 'admission_number', 'guardian_phone')
    # Group fields in the editor for better UX
    fieldsets = (
        ('Student Info', {'fields': ('photo', 'first_name', 'last_name', 'classroom', 'gender', 'date_of_birth')}),
        ('Guardian Info', {'fields': ('guardian_name', 'guardian_relation', 'guardian_phone', 'guardian_email', 'guardian_address')}),
        ('Status', {'fields': ('is_active',)}),
    )