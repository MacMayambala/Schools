from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
import tablib
from .models import Student, Classroom
from django.contrib.auth.mixins import LoginRequiredMixin # 👈 Add this import

# students/views.py
# students/views.py
from django.views.generic import ListView
from .models import Student
from django.views.generic import ListView
from django.db.models import Q
from .models import Student, Classroom

class StudentListView(ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 50  # Increased for better administrative overview

    def get_queryset(self):
        # 1. Base Queryset with Multi-Tenant isolation
        # Optimization: select_related performs a SQL JOIN for foreign keys
        queryset = Student.objects.filter(school=self.request.school)\
            .select_related('classroom', 'stream')\
            .prefetch_related('invoices')\
            .order_by('-date_enrolled')

        # 2. Get Filter Params from URL
        query = self.request.GET.get('q')
        class_id = self.request.GET.get('class')

        # 3. Apply Search Logic
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query) | 
                Q(admission_number__icontains=query) |
                Q(guardian_phone__icontains=query) # Added phone search for easier lookups
            )

        # 4. Apply Classroom Filter
        if class_id:
            queryset = queryset.filter(classroom_id=class_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Pull filters for the dropdowns
        context['classrooms'] = Classroom.objects.filter(school=self.request.school)
        
        # Send current filter values back to template to keep inputs populated
        context['query'] = self.request.GET.get('q', '')
        context['selected_class'] = self.request.GET.get('class', '')
        
        return context
    



import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import Student, Classroom
from .forms import StudentForm  # Use the form we built to handle validation

# 1. CREATE STUDENT
class StudentCreateView(LoginRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm # Using the Form class is better than 'fields' for complex models
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:student_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['school'] = self.request.school # Pass school to filter classrooms in the form
        return kwargs

    def form_valid(self, form):
        form.instance.school = self.request.school
        messages.success(self.request, f"Student {form.instance.get_full_name()} added successfully.")
        return super().form_valid(form)

# 2. UPDATE STUDENT
class StudentUpdateView(LoginRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:student_list')

    def get_queryset(self):
        return Student.objects.filter(school=self.request.school)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['school'] = self.request.school
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Student details updated successfully!")
        return super().form_valid(form)

# 3. BULK IMPORT (Updated for Guardian Details)
def bulk_import_students(request):
    if request.method == "POST" and request.FILES.get('excel_file'):
        file = request.FILES['excel_file']
        try:
            df = pd.read_excel(file)
            count = 0
            for _, row in df.iterrows():
                # Find classroom by name
                classroom = Classroom.objects.filter(
                    name__iexact=str(row['Classroom']).strip(), 
                    school=request.school
                ).first()
                
                if classroom:
                    Student.objects.create(
                        school=request.school,
                        first_name=row['First Name'],
                        last_name=row['Last Name'],
                        classroom=classroom,
                        gender=row.get('Gender', 'M'),
                        guardian_name=row.get('Guardian Name', 'Not Provided'),
                        guardian_phone=row.get('Guardian Phone', '0000000000'),
                        guardian_relation=row.get('Relationship', 'FATHER'),
                    )
                    count += 1
            
            messages.success(request, f"Successfully imported {count} students!")
            return redirect('students:student_list')
        except Exception as e:
            messages.error(request, f"Error processing Excel file: {e}")

    return render(request, 'students/bulk_import.html')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Student, Classroom
from django.db import transaction

def promote_students_view(request):
    # Fetch all students and classes for the school
    students = Student.objects.filter(school=request.school, is_active=True).select_related('classroom')
    classrooms = Classroom.objects.filter(school=request.school).order_by('level')
    
    if request.method == "POST":
        student_ids = request.POST.getlist('student_ids')
        target_class_id = request.POST.get('target_class')
        
        if not student_ids:
            messages.error(request, "No students were selected for promotion.")
            return redirect('students:promote_students')
            
        if not target_class_id:
            messages.error(request, "Please select a target class.")
            return redirect('students:promote_students')

        target_class = get_object_or_404(Classroom, id=target_class_id, school=request.school)

        try:
            with transaction.atomic():
                # Perform the update
                updated_count = Student.objects.filter(
                    id__in=student_ids, 
                    school=request.school
                ).update(classroom=target_class)
                
                messages.success(request, f"Successfully promoted {updated_count} students to {target_class.name}.")
                return redirect('students:student_list') # Redirect back to registry
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    return render(request, 'students/promote.html', {
        'students': students,
        'classrooms': classrooms
    })

import openpyxl
from django.http import HttpResponse
from .models import Classroom

def download_student_import_template(request):
    # Create a workbook and select the active worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Student Import Template"

    # Define the headers exactly as expected by your bulk_import_students view
    headers = [
        'First Name', 'Last Name', 'Classroom', 
        'Gender', 'Guardian Name', 'Guardian Phone', 'Relationship'
    ]
    ws.append(headers)

    # Optional: Add some sample data and instructions
    # We can pull existing classroom names to show the user what to type
    classrooms = Classroom.objects.filter(school=request.school).values_list('name', flat=True)
    valid_classes = ", ".join(classrooms) if classrooms else "e.g., Senior One"

    ws.append(['John', 'Doe', classrooms[0] if classrooms else 'Senior One', 'M', 'Jane Doe', '0700123456', 'MOTHER'])
    
    # Add a small instruction note at the bottom
    ws.append([])
    ws.append([f"Note: Classroom names must match exactly: {valid_classes}"])

    # Prepare the response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename=student_import_template.xlsx'
    wb.save(response)
    return response



from django.shortcuts import redirect
from django.contrib import messages
from .models import Student
from django.shortcuts import redirect
from django.contrib import messages
from django.db import transaction
from .models import Student, Classroom

def student_bulk_action(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        student_ids = request.POST.getlist('student_ids')

        if not student_ids:
            messages.warning(request, "Please select at least one student.")
            return redirect('students:student_list')

        # Filter students strictly by the current logged-in school for security
        queryset = Student.objects.filter(id__in=student_ids, school=request.school)

        if action == 'delete':
            count = queryset.count()
            queryset.delete()
            messages.success(request, f"Successfully removed {count} student records.")

        elif action == 'promote':
            promoted_count = 0
            skipped_count = 0
            
            # Use a transaction so either everyone is promoted or no one is (in case of error)
            with transaction.atomic():
                for student in queryset:
                    current_class = student.classroom
                    
                    # Logic: Find the class with the next level up in the same school
                    # This assumes your Classroom model has a 'level' integer field
                    next_class = Classroom.objects.filter(
                        school=request.school,
                        level__gt=current_class.level
                    ).order_by('level').first()

                    if next_class:
                        student.classroom = next_class
                        student.save()
                        promoted_count += 1
                    else:
                        skipped_count += 1

            if promoted_count > 0:
                messages.success(request, f"Successfully promoted {promoted_count} students.")
            if skipped_count > 0:
                messages.warning(request, f"{skipped_count} students were already in the highest class (e.g., Senior 6) and couldn't be promoted.")

        elif action == 'generate_invoices':
            # This would link to your finance logic to create termly bills
            messages.info(request, "Invoice generation logic triggered for selected students.")

    return redirect('students:student_list')



from django.shortcuts import redirect
from django.contrib import messages
from .models import Student
from finance.models import Invoice, FeeStructure
from django.db import transaction
@transaction.atomic
def student_bulk_action(request):
    if request.method == "POST":
        student_ids = request.POST.getlist('student_ids')
        action = request.POST.get('action')
        
        queryset = Student.objects.filter(id__in=student_ids, school=request.school)

        if action == "promote":
            promoted_count = 0
            skipped_count = 0
            
            for student in queryset:
                current_level = student.classroom.level
                next_level = current_level + 1
                
                # Find the class in THIS school that matches the next level
                target_class = Classroom.objects.filter(
                    school=request.school, 
                    level=next_level
                ).first()

                if target_class:
                    student.classroom = target_class
                    student.save() # Triggers any specific logic you have in save()
                    promoted_count += 1
                else:
                    # This happens if they are in the highest class (e.g., P.7)
                    skipped_count += 1

            if promoted_count > 0:
                messages.success(request, f"Successfully promoted {promoted_count} students to the next level.")
            if skipped_count > 0:
                messages.warning(request, f"{skipped_count} students could not be promoted (No higher class level found).")

        elif action == "generate_invoices":
            # ... (your invoicing logic)
            pass

    return redirect('students:student_list')

@transaction.atomic
def handle_bulk_invoicing(request, students):
    """Integrates with the finance logic we built earlier"""
    count = 0
    # Assuming we are billing for current active term/year
    # In a real scenario, you might want a modal to pick the term first
    term, year = "1", 2026 
    
    for student in students:
        structure = FeeStructure.objects.filter(
            classroom=student.classroom, 
            section=student.section,
            term=term,
            year=year
        ).first()

        if structure:
            _, created = Invoice.objects.get_or_create(
                student=student,
                term=term,
                year=year,
                school=request.school,
                defaults={'total_amount': structure.total_fees}
            )
            if created: count += 1

    messages.success(request, f"Generated {count} invoices for selected students.")
    return redirect('students:registry')