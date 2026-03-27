from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .models import Mark, Subject, Teacher
from students.models import Student, Classroom

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Classroom, Subject, Student, Mark, SubjectAssignment

def enter_marks(request, classroom_id, subject_id):
    # 1. Fetch data with school-scoping for security
    classroom = get_object_or_404(Classroom, id=classroom_id, school=request.school)
    subject = get_object_or_404(Subject, id=subject_id, school=request.school)
    
    # 2. STRICT SECURITY: Verify Teacher Assignment
    if not request.user.is_superuser:
        try:
            teacher_profile = request.user.teacher_profile
            is_assigned = SubjectAssignment.objects.filter(
                teacher=teacher_profile,
                subject=subject,
                classroom=classroom,
                year=2026
            ).exists()
            
            if not is_assigned:
                messages.error(request, f"Access Denied: You are not the assigned teacher for {subject.name} in {classroom.name}.")
                return redirect('academic:dashboard')
        except AttributeError:
            messages.error(request, "Only registered teachers can access this page.")
            return redirect('academic:dashboard')

    # 3. Fetch students efficiently
    students = Student.objects.filter(classroom=classroom, school=request.school)
    
    if request.method == "POST":
        term = request.POST.get('term')
        
        # 4. Atomic-style loop for mark entry
        for student in students:
            mid_val = request.POST.get(f'mid_{student.id}')
            end_val = request.POST.get(f'end_{student.id}')
            
            # Clean empty strings to None (prevents database float errors)
            mid_mark = float(mid_val) if mid_val and mid_val.strip() else None
            end_mark = float(end_val) if end_val and end_val.strip() else None
            
            Mark.objects.update_or_create(
                student=student,
                subject=subject,
                classroom=classroom,
                school=request.school,
                term=term,
                year=2026,
                defaults={
                    'mid_term_mark': mid_mark,
                    'end_term_mark': end_mark,
                    'entered_by': request.user, # Track who did the work
                }
            )
        
        messages.success(request, f"Marks for {subject.name} in {classroom.name} have been updated successfully.")
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

from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from .models import Mark, Subject
from students.models import Student
# Assuming get_class_ranking is in your utils.py
from .utils import get_class_ranking 
def student_report_card(request, student_id, term, year):
    student = get_object_or_404(Student, id=student_id, school=request.school)
    
    # URL sends "Term-1", DB needs "1"
    clean_term = term.replace("Term-", "").strip() 

    marks = Mark.objects.filter(
        student=student, 
        term=clean_term, 
        year=year,
        school=request.school
    ).select_related('subject')

    # Aggregates
    all_scores = [m.total_score for m in marks if m.total_score is not None]
    average = sum(all_scores) / len(all_scores) if all_scores else 0
    
    # Ranks (Using the helper function you likely have)
    class_ranks = get_class_ranking(student.classroom, clean_term, year)
    my_rank = class_ranks.get(student.id, "N/A")

    context = {
        'student': student,
        'marks': marks,
        'term': term,
        'year': year,
        'rank': my_rank,
        'average': average,
        'total_students': len(class_ranks),
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


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Teacher
from django.utils import timezone
@login_required
def teacher_dashboard(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    my_classes = teacher.classrooms.all().prefetch_related('subjects')
    my_subjects = teacher.subjects.all()
    
    # Calculate total students safely
    total_students = 0
    for classroom in my_classes:
        # Check which one works for your model: .students or .student_set
        if hasattr(classroom, 'students'):
            total_students += classroom.students.count()
        elif hasattr(classroom, 'student_set'):
            total_students += classroom.student_set.count()

    context = {
        'teacher': teacher,
        'my_classes': my_classes,
        'my_subjects': my_subjects,
        'total_students': total_students,
        'today': timezone.now(),
    }
    return render(request, 'teachers/dashboard.html', context)




from django.core.paginator import Paginator
from django.db.models import Q

from django.core.paginator import Paginator
from django.db.models import Q

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Teacher

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Teacher

def teacher_directory(request):
    # 1. Get the search term and clean it
    query = request.GET.get('q', '').strip()
    
    # 2. MULTI-TENANT SECURITY CHECK
    # Check if the user has a profile and an assigned school
    if not hasattr(request.user, 'teacher_profile'):
        messages.error(request, f"Access Denied: The account '{request.user.username}' is not linked to any school profile. Please contact MAC Technologies support.")
        return redirect('/') # Redirect to home instead of crashing on a 403 template

    user_school = request.user.teacher_profile.school
    
    # 3. Fetch ONLY teachers belonging to this school
    teacher_list = Teacher.objects.filter(school=user_school).select_related('user').prefetch_related('subjects', 'classrooms')

    # 4. Apply Search Filter
    if query:
        teacher_list = teacher_list.filter(
            Q(user__first_name__icontains=query) | 
            Q(user__last_name__icontains=query) |
            Q(staff_id__icontains=query)
        )

    # 5. Setup Pagination (12 cards per page)
    paginator = Paginator(teacher_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'total_count': teacher_list.count(),
        'current_school': user_school,
    }
    return render(request, 'teachers/directory.html', context)
