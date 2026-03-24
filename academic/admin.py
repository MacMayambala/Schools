from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Subject, Mark

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'school')
    search_fields = ('name', 'code')

# academic/admin.py
@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'total_score', 'grade', 'term', 'year')
    list_filter = ('term', 'year', 'classroom', 'subject')
    search_fields = ('student__first_name', 'student__last_name')