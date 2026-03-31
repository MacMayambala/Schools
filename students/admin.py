from django.contrib import admin
from .models import Student, Classroom, Stream

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'level', 'school')
    list_filter = ('school',)
    search_fields = ('name', 'short_name')
    ordering = ('school', 'level')

    def save_model(self, request, obj, form, change):
        if not obj.school and hasattr(request, 'school'):
            obj.school = request.school
        super().save_model(request, obj, form, change)

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('name', 'school')
    list_filter = ('school',)
    search_fields = ('name',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    # Added Stream and Section to the display
    list_display = (
        'admission_number', 
        'first_name', 
        'last_name', 
        'classroom', 
        'stream', 
        'section', 
        'is_active'
    )
    
    list_filter = ('school', 'classroom', 'stream', 'section', 'gender', 'is_active')
    search_fields = ('first_name', 'last_name', 'admission_number', 'guardian_phone')
    readonly_fields = ('admission_number', 'date_enrolled')

    fieldsets = (
        ('Academic Placement', {
            'fields': ('school', 'classroom', 'stream', 'section')
        }),
        ('Personal Details', {
            'fields': ('photo', 'first_name', 'last_name', 'gender', 'date_of_birth', 'admission_number')
        }),
        ('Guardian Information', {
            'fields': (
                'guardian_name', 'guardian_relation', 'guardian_phone', 
                'guardian_email', 'guardian_address'
            ),
            'classes': ('collapse',),
        }),
        ('System Metadata', {
            'fields': ('is_active', 'date_enrolled'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.school and hasattr(request, 'school'):
            obj.school = request.school
        super().save_model(request, obj, form, change)