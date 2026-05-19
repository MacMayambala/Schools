from django.contrib import admin
from .models import Student, Classroom, Stream, ClassStream

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

    def save_model(self, request, obj, form, change):
        if not obj.school and hasattr(request, 'school'):
            obj.school = request.school
        super().save_model(request, obj, form, change)

@admin.register(ClassStream)
class ClassStreamAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'classroom', 'stream', 'class_teacher', 'capacity', 'is_active', 'school')
    list_filter = ('school', 'classroom', 'is_active')
    search_fields = ('classroom__name', 'stream__name', 'room_number')

    def save_model(self, request, obj, form, change):
        if not obj.school and hasattr(request, 'school'):
            obj.school = request.school
        super().save_model(request, obj, form, change)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    # Fixed: Use methods to display classroom and stream from the junction model
    list_display = (
        'admission_number', 
        'first_name', 
        'last_name', 
        'get_classroom', 
        'get_stream', 
        'section', 
        'is_active'
    )
    
    # Fixed: Use double underscore (__) to filter through the class_stream relationship
    list_filter = (
        'school', 
        'class_stream__classroom', 
        'class_stream__stream', 
        'section', 
        'gender', 
        'is_active'
    )
    
    search_fields = ('first_name', 'last_name', 'admission_number', 'guardian_phone')
    readonly_fields = ('admission_number', 'date_enrolled')

    fieldsets = (
        ('Academic Placement', {
            'fields': ('school', 'class_stream', 'section')
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

    # Helper methods for list_display
    @admin.display(ordering='class_stream__classroom', description='Class')
    def get_classroom(self, obj):
        return obj.class_stream.classroom.short_name if obj.class_stream else "-"

    @admin.display(ordering='class_stream__stream', description='Stream')
    def get_stream(self, obj):
        return obj.class_stream.stream.name if obj.class_stream else "-"

    def save_model(self, request, obj, form, change):
        if not obj.school and hasattr(request, 'school'):
            obj.school = request.school
        super().save_model(request, obj, form, change)