# core/admin.py
from django.contrib import admin
from .models import School

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    # Change 'school_code' to 'code'
    list_display = ('name', 'code', 'admin') 
    search_fields = ('name', 'code')