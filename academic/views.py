from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .models import Mark, Subject
from students.models import Student, Classroom

def enter_marks(request, classroom_id, subject_id):
    classroom = Classroom.objects.get(id=classroom_id, school=request.school)
    subject = Subject.objects.get(id=subject_id, school=request.school)
    students = Student.objects.filter(classroom=classroom, school=request.school)
    
    if request.method == "POST":
        for student in students:
            mid_mark = request.POST.get(f'mid_{student.id}')
            end_mark = request.POST.get(f'end_{student.id}')
            
            Mark.objects.update_or_create(
                student=student,
                subject=subject,
                classroom=classroom,
                school=request.school,
                term=request.POST.get('term'),
                year=2026,
                defaults={
                    'mid_term_mark': mid_mark if mid_mark else None,
                    'end_term_mark': end_mark if end_mark else None,
                }
            )
        return redirect('academic:dashboard')

    return render(request, 'academic/mark_sheet.html', {
        'classroom': classroom,
        'subject': subject,
        'students': students
    })


from django.shortcuts import render, get_object_or_404
from .models import Mark, Subject
from .utils import get_class_ranking
from students.models import Student

def student_report_card(request, student_id, term, year):
    student = get_object_or_404(Student, id=student_id, school=request.school)
    marks = Mark.objects.filter(student=student, term=term, year=year)
    
    # Calculate Ranks
    class_ranks = get_class_ranking(student.classroom, term, year)
    my_rank = class_ranks.get(student.id, "N/A")
    total_students = len(class_ranks)

    context = {
        'student': student,
        'marks': marks,
        'term': term,
        'year': year,
        'rank': my_rank,
        'total_students': total_students,
        'school': request.school
    }
    return render(request, 'academic/report_card.html', context)


from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Mark
from students.models import Student

from django.db.models import Avg

def generate_report_card(request, student_id, term, year):
    student = get_object_or_404(Student, id=student_id, school=request.school)
    marks = Mark.objects.filter(student=student, term=term, year=year)
    
    # Calculate the average across all subjects
    # This uses Django's Avg function on the 'total_score' isn't possible directly 
    # since it's a property, so we do it in Python:
    all_scores = [m.total_score for m in marks if m.total_score]
    average = sum(all_scores) / len(all_scores) if all_scores else 0

    context = {
        'student': student,
        'marks': marks, # This matches your new loop
        'average': average,
        'term_name': f"Term {term}",
        'year': year,
        'school': request.school,
    }
    return render(request, 'academic/report_card.html', context)


# academic/views.py
from django.shortcuts import render
from students.models import Classroom # Assuming your model name

def academic_dashboard(request):
    # Tenancy Check: Only show classes for the logged-in school
    classrooms = Classroom.objects.filter(school=request.school)
    
    context = {
        'classrooms': classrooms,
    }
    return render(request, 'academic/dashboard.html', context)


from django.db.models import Sum

from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from .models import Mark
from students.models import Student

def student_report_card(request, student_id, term, year):
    # 1. Fetch Student and their Marks
    student = get_object_or_404(Student, id=student_id)
    marks = Mark.objects.filter(student=student, term=term, year=year)
    
    # 2. Calculate Rank (Compare against all students in the same class)
    # Get all marks for this class/term/year
    all_class_marks = Mark.objects.filter(
        classroom=student.classroom, 
        term=term, 
        year=year
    )
    
    # Group totals by student ID
    student_totals = {}
    for m in all_class_marks:
        if m.student_id not in student_totals:
            student_totals[m.student_id] = 0
        student_totals[m.student_id] += float(m.total_score)
    
    # Sort totals descending to determine position
    sorted_scores = sorted(student_totals.values(), reverse=True)
    my_total = student_totals.get(student.id, 0)
    
    # Position logic
    if my_total > 0:
        rank = sorted_scores.index(my_total) + 1
    else:
        rank = "N/A"

    # 3. Calculate Personal Average
    all_scores = [float(m.total_score) for m in marks]
    average = sum(all_scores) / len(all_scores) if all_scores else 0

    context = {
        'student': student,
        'marks': marks,
        'average': average,
        'rank': rank,
        'total_students': len(student_totals),
        'school': request.school, # Assumes core.context_processors.school_context provides this
        'term': term,
        'year': year,
    }
    return render(request, 'academic/report_card.html', context)



from .forms import SubjectForm

def manage_subjects(request):
    subjects = Subject.objects.filter(school=request.school)
    
    if request.method == "POST":
        form = SubjectForm(request.POST, school=request.school)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.school = request.school # Auto-link to the Tenant
            subject.save()
            form.save_m2m() # Important for ManyToMany classrooms!
            return redirect('academic:manage_subjects')
    else:
        form = SubjectForm(school=request.school)

    return render(request, 'academic/manage_subjects.html', {
        'subjects': subjects,
        'form': form
    })