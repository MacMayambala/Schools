from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import Mark, Subject, Classroom, SubjectAssignment
from students.models import Student

def enter_marks(request, classroom_id, subject_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, school=request.school)
    subject = get_object_or_404(Subject, id=subject_id, school=request.school)
    
    # Allow dynamic selection of term/year from GET or default to current
    selected_term = request.GET.get('term', 'Term 1')
    selected_year = int(request.GET.get('year', timezone.now().year))
    
    # 1. SECURITY: Superuser or Assigned Teacher
    if not request.user.is_superuser:
        teacher_profile = getattr(request.user, 'teacher_profile', None)
        if not teacher_profile:
            messages.error(request, "Teacher Profile missing.")
            return redirect('academic:dashboard')

        is_assigned = SubjectAssignment.objects.filter(
            teacher=teacher_profile, subject=subject,
            classroom=classroom, year=selected_year
        ).exists()

        if not is_assigned:
            messages.error(request, f"Access Denied for {subject.name} in {selected_year}.")
            return redirect('academic:dashboard')

    # 2. Fetch students and existing marks for this specific term/year
    students = Student.objects.filter(classroom=classroom, school=request.school, is_active=True)
    
    # Map existing marks to a dictionary {student_id: mark_object} for easy lookup in template
    existing_marks = {
        m.student_id: m for m in Mark.objects.filter(
            subject=subject, term=selected_term, year=selected_year
        )
    }

    if request.method == "POST":
        post_term = request.POST.get('term')
        post_year = int(request.POST.get('year'))
        
        try:
            with transaction.atomic():
                for student in students:
                    mid_val = request.POST.get(f'mid_{student.id}')
                    end_val = request.POST.get(f'end_{student.id}')
                    
                    def to_float(val):
                        try:
                            return float(val) if val and str(val).strip() else None
                        except (ValueError, TypeError):
                            return None

                    Mark.objects.update_or_create(
                        student=student, subject=subject,
                        classroom=classroom, school=request.school,
                        term=post_term, year=post_year,
                        defaults={
                            'mid_term_mark': to_float(mid_val),
                            'end_term_mark': to_float(end_val),
                            'entered_by': request.user,
                        }
                    )
            
            messages.success(request, f"Marks saved for {post_term} {post_year}.")
            return redirect('academic:dashboard')
            
        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, 'academic/mark_sheet.html', {
        'classroom': classroom,
        'subject': subject,
        'students': students,
        'existing_marks': existing_marks,
        'selected_term': selected_term,
        'selected_year': selected_year,
        'years': range(2024, timezone.now().year + 2) # List for year dropdown
    })

from django.shortcuts import render, get_object_or_404
from .models import Mark, Subject
from .utils import get_class_ranking
from students.models import Student
from .models import Mark, ClassRequirement
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.template.loader import get_template
from io import BytesIO

# pip install xhtml2pdf
from xhtml2pdf import pisa


def student_report_card(request, student_id, term, year):
    student = get_object_or_404(Student, id=student_id, school=request.school)

    # ✅ Normalize
    clean_term = term.replace("Term-", "").strip()
    try:
        clean_year = int(year)
    except (ValueError, TypeError):
        clean_year = 2026

    # ✅ Fetch marks
    marks = Mark.objects.filter(
        student=student,
        term=clean_term,
        year=clean_year,
        school=request.school
    ).select_related('subject')

    # ✅ Calculate Average
    scores = [m.total_score for m in marks if m.total_score is not None]
    average = sum(scores) / len(scores) if scores else 0

    # ✅ Requirements Logic
    next_term_map = {"1": "2", "2": "3", "3": "1"}
    target_term = next_term_map.get(clean_term, "1")
    target_year = clean_year + 1 if clean_term == "3" else clean_year

    requirements = ClassRequirement.objects.filter(
        classroom=student.classroom,
        term=target_term,
        year=target_year,
        school=request.school
    ).first()

    # ✅ Rank Logic
    class_marks = Mark.objects.filter(
        classroom=student.classroom,
        term=clean_term,
        year=clean_year,
        school=request.school
    )
    totals = {}
    for m in class_marks:
        score_to_add = m.total_score if m.total_score is not None else 0
        totals[m.student_id] = totals.get(m.student_id, 0) + score_to_add

    sorted_totals = sorted(list(totals.values()), reverse=True)
    my_total = totals.get(student.id, 0)
    rank = sorted_totals.index(my_total) + 1 if my_total > 0 else "N/A"

    # ✅ Division Helper
    def get_division(student_marks):
        if not student_marks:
            return "N/A"
        grade_map = {
            'D1': 1, 'D2': 2, 'C3': 3, 'C4': 4,
            'C5': 5, 'C6': 6, 'P7': 7, 'P8': 8, 'F9': 9
        }
        points = [grade_map.get(m.grade, 9) for m in student_marks]
        points.sort()
        agg = sum(points[:8])
        if agg <= 12:
            return "Division 1"
        elif agg <= 24:
            return "Division 2"
        elif agg <= 34:
            return "Division 3"
        return "Division 4"

    # ✅ Comment Helper
    def get_teacher_comment(avg):
        if avg >= 75:
            return "An excellent result. Keep it up!"
        if avg >= 60:
            return "Good performance, but aim higher."
        if avg >= 45:
            return "Fairly good, more effort is needed."
        return "Poor performance. Please double your efforts."

    context = {
        'student': student,
        'marks': marks,
        'average': average,
        'rank': rank,
        'total_students': len(totals),
        'term': f"Term {clean_term}",
        'year': clean_year,
        'target_term': target_term,
        'school': request.school,
        'division': get_division(marks),
        'teacher_comment': get_teacher_comment(average),
        'requirements': requirements,
        'is_pdf': False,  # flag for template
    }

    # ✅ PDF Download — triggered by ?download=pdf
    if request.GET.get('download') == 'pdf':
        context['is_pdf'] = True
        template = get_template('academic/report_card.html')
        html = template.render(context, request)

        buffer = BytesIO()
        pdf = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=buffer)

        if pdf.err:
            return HttpResponse("Error generating PDF. Please try again.", status=500)

        # File named: StudentName_Term1_2026.pdf
        safe_name = student.get_full_name().replace(" ", "_")
        filename = f"{safe_name}_Term{clean_term}_{clean_year}.pdf"

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    # ✅ Normal HTML preview
    return render(request, 'academic/report_card.html', context)

# from django.shortcuts import get_object_or_404
# from django.http import HttpResponse
# from django.template.loader import get_template
# from xhtml2pdf import pisa
# from .models import Mark
# from students.models import Student

# from django.db.models import Avg

# def generate_report_card(request, student_id, term, year):
#     student = get_object_or_404(Student, id=student_id, school=request.school)
#     marks = Mark.objects.filter(student=student, term=term, year=year)
    
#     # Calculate the average across all subjects
#     # This uses Django's Avg function on the 'total_score' isn't possible directly 
#     # since it's a property, so we do it in Python:
#     all_scores = [m.total_score for m in marks if m.total_score]
#     average = sum(all_scores) / len(all_scores) if all_scores else 0

#     context = {
#         'student': student,
#         'marks': marks, # This matches your new loop
#         'average': average,
#         'term_name': f"Term {term}",
#         'year': year,
#         'school': request.school,
#     }
#     return render(request, 'academic/report_card.html', context)


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


# from django.db.models import Sum

# from django.shortcuts import render, get_object_or_404
# from django.db.models import Sum
# from .models import Mark
# from students.models import Student

# def student_report_card(request, student_id, term, year):
#     # 1. Fetch Student and their Marks
#     student = get_object_or_404(Student, id=student_id)
#     marks = Mark.objects.filter(student=student, term=term, year=year)
    
#     # 2. Calculate Rank (Compare against all students in the same class)
#     # Get all marks for this class/term/year
#     all_class_marks = Mark.objects.filter(
#         classroom=student.classroom, 
#         term=term, 
#         year=year
#     )
    
#     # Group totals by student ID
#     student_totals = {}
#     for m in all_class_marks:
#         if m.student_id not in student_totals:
#             student_totals[m.student_id] = 0
#         student_totals[m.student_id] += float(m.total_score)
    
#     # Sort totals descending to determine position
#     sorted_scores = sorted(student_totals.values(), reverse=True)
#     my_total = student_totals.get(student.id, 0)
    
#     # Position logic
#     if my_total > 0:
#         rank = sorted_scores.index(my_total) + 1
#     else:
#         rank = "N/A"

#     # 3. Calculate Personal Average
#     all_scores = [float(m.total_score) for m in marks]
#     average = sum(all_scores) / len(all_scores) if all_scores else 0

#     context = {
#         'student': student,
#         'marks': marks,
#         'average': average,
#         'rank': rank,
#         'total_students': len(student_totals),
#         'school': request.school, # Assumes core.context_processors.school_context provides this
#         'term': term,
#         'year': year,
#     }
#     return render(request, 'academic/report_card.html', context)



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



from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Teacher, Subject
from students.models import Classroom

# @require_POST
# def update_teacher_assignments(request, teacher_id):
#     # Security: Ensure the teacher belongs to the user's school
#     teacher = get_object_or_404(Teacher, id=teacher_id, school=request.school)
    
#     # Get lists of IDs from the form
#     subject_ids = request.POST.getlist('subjects')
#     classroom_ids = request.POST.getlist('classrooms')

#     # Update ManyToMany relationships
#     teacher.subjects.set(Subject.objects.filter(id__in=subject_ids, school=request.school))
#     teacher.classrooms.set(Classroom.objects.filter(id__in=classroom_ids, school=request.school))
    
#     messages.success(request, f"Assignments for {teacher.user.get_full_name()} updated successfully.")
#     return redirect(request.META.get('HTTP_REFERER', 'academic:teacher_directory'))

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect

@require_POST
def add_teacher(request):
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    email = request.POST.get('email')
    staff_id = request.POST.get('staff_id')
    phone = request.POST.get('phone')
    create_account = request.POST.get('create_account') == 'on'

    user = None
    if create_account and email:
        if User.objects.filter(username=email).exists():
            messages.error(request, f"A user with email {email} already exists.")
            return redirect('academic:teacher_directory')
        
        # 1. Create the User Account
        user = User.objects.create_user(
            username=email,
            email=email,
            password=staff_id, # Using Staff ID as initial password
            first_name=first_name,
            last_name=last_name
        )

        # 2. Send the Welcome Email
        subject = f"Welcome to {request.school.name} Portal"
        message = f"""
        Hello {first_name},

        An account has been created for you on the {request.school.name} management system.
        
        Your login credentials are:
        Username: {email}
        Password: {staff_id}
        
        You can log in here: {request.build_absolute_uri('/')}
        
        Please change your password after your first login for security purposes.
        """
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            # We log the error but don't stop the process
            messages.warning(request, "Teacher added, but the welcome email failed to send. Please check your SMTP settings.")

    # 3. Create Teacher Record (Linked to user if created, else None)
    Teacher.objects.create(
        school=request.school,
        user=user,
        first_name=first_name,
        last_name=last_name,
        staff_id=staff_id,
        phone=phone
    )

    messages.success(request, f"Teacher {first_name} {last_name} has been successfully registered.")
    return redirect('academic:teacher_directory')


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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import Teacher, Subject
from students.models import Classroom

def teacher_directory(request):
    query = request.GET.get('q', '').strip()
    
    # 1. Multi-Tenant Security Check
    if not hasattr(request.user, 'teacher_profile'):
        messages.error(request, f"Access Denied: Account '{request.user.username}' is not linked to a school profile.")
        return redirect('/')

    user_school = request.user.teacher_profile.school
    
    # 2. Fetch School-Specific Data
    teacher_list = Teacher.objects.filter(school=user_school).select_related('user').prefetch_related('subjects', 'classrooms')
    all_subjects = Subject.objects.filter(school=user_school)
    all_classrooms = Classroom.objects.filter(school=user_school)

    # 3. Apply Search Filter
    if query:
        teacher_list = teacher_list.filter(
            Q(user__first_name__icontains=query) | 
            Q(user__last_name__icontains=query) |
            Q(staff_id__icontains=query)
        )

    # 4. Pagination
    paginator = Paginator(teacher_list, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'query': query,
        'total_count': teacher_list.count(),
        'current_school': user_school,
        'all_subjects': all_subjects,
        'all_classrooms': all_classrooms,
    }
    return render(request, 'teachers/directory.html', context)

@require_POST
def update_teacher_assignments(request, teacher_id):
    """Front-end logic to assign subjects/classes to a teacher"""
    teacher = get_object_or_404(Teacher, id=teacher_id, school=request.school)
    
    subject_ids = request.POST.getlist('subjects')
    classroom_ids = request.POST.getlist('classrooms')

    # Update ManyToMany relationships safely
    teacher.subjects.set(Subject.objects.filter(id__in=subject_ids, school=request.school))
    teacher.classrooms.set(Classroom.objects.filter(id__in=classroom_ids, school=request.school))
    
    messages.success(request, f"Assignments for {teacher.user.get_full_name()} updated successfully.")
    return redirect('academic:teacher_directory')



from django.shortcuts import redirect
from django.contrib import messages
from .models import ClassRequirement

def create_requirement(request):
    if request.method == "POST":
        classroom_id = request.POST.get('classroom')
        term = request.POST.get('term')
        year = request.POST.get('year')
        items = request.POST.get('items')

        ClassRequirement.objects.create(
            school=request.school,
            classroom_id=classroom_id,
            term=term,
            year=year,
            items=items
        )
        messages.success(request, "Requirements updated successfully!")
    
    # Redirect back to where the request came from (Settings Hub)
    return redirect(request.META.get('HTTP_REFERER', 'finance:settings'))




from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

def teacher_status_toggle(request, pk):
    """AJAX view to activate/deactivate teacher"""
    teacher = get_object_or_404(Teacher, pk=pk, school=request.school)
    # Assuming is_active is on the User model
    user = teacher.user
    user.is_active = not user.is_active
    user.save()
    
    return JsonResponse({
        'status': 'success',
        'is_active': user.is_active,
        'message': f"Teacher {user.get_full_name()} updated."
    })

def teacher_edit(request, pk):
    """View to handle profile updates with optional User accounts"""
    # Ensure the teacher belongs to the current school context
    teacher = get_object_or_404(Teacher, pk=pk, school=request.school)
    
    if request.method == "POST":
        # 1. Update the Teacher model fields (These always exist)
        teacher.first_name = request.POST.get('first_name')
        teacher.last_name = request.POST.get('last_name')
        teacher.phone = request.POST.get('phone')
        
        if request.FILES.get('profile_photo'):
            teacher.profile_photo = request.FILES.get('profile_photo')
            
        teacher.save()

        # 2. Update the User account ONLY if it is linked
        if teacher.user:
            teacher.user.first_name = request.POST.get('first_name')
            teacher.user.last_name = request.POST.get('last_name')
            teacher.user.save()
            
        messages.success(request, f"Profile for {teacher.get_full_name} updated successfully.")
        return redirect('academic:teacher_directory')
    
    return render(request, 'academic/teachers/edit_partial.html', {'teacher': teacher})




from django.shortcuts import render, get_object_or_404
from collections import defaultdict
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count
from collections import defaultdict

from django.shortcuts import render, get_object_or_404
from collections import defaultdict
from django.shortcuts import render, get_object_or_404
from collections import defaultdict

from django.shortcuts import render, get_object_or_404
from collections import defaultdict

def get_division_and_aggregate(marks_list):
    """Calculate Division and Aggregate (best 8 subjects)"""
    if not marks_list or len(marks_list) == 0:
        return "N/A", 0
    
    grade_map = {
        'D1': 1, 'D2': 2, 'C3': 3, 'C4': 4,
        'C5': 5, 'C6': 6, 'P7': 7, 'P8': 8, 'F9': 9, 'F': 9
    }
    
    points = [grade_map.get(mark.grade, 9) for mark in marks_list]
    points.sort()                    # Best grades first
    best_8 = points[:8]
    aggregate = sum(best_8)
    
    if aggregate <= 12:
        division = "Division 1"
    elif aggregate <= 24:
        division = "Division 2"
    elif aggregate <= 34:
        division = "Division 3"
    else:
        division = "Division 4"
    
    return division, aggregate


def student_report_history(request, student_id):
    student = get_object_or_404(Student, id=student_id, school=request.school)
    
    marks_queryset = Mark.objects.filter(
        student=student
    ).select_related('subject').order_by('-year', 'term')

    structured_history = defaultdict(lambda: defaultdict(list))
    term_aggregates = defaultdict(dict)

    for mark in marks_queryset:
        structured_history[mark.year][mark.term].append(mark)

    # Calculate aggregates + Division + Total Points
    for year, terms in structured_history.items():
        for term, marks_list in terms.items():
            if marks_list:
                total = sum(m.total_score for m in marks_list)
                count = len(marks_list)
                average = round(total / count, 1) if count > 0 else 0
                
                division, aggregate_points = get_division_and_aggregate(marks_list)
                
                term_aggregates[year][term] = {
                    'average': average,
                    'subject_count': count,
                    'division': division,
                    'aggregate_points': aggregate_points,
                }

    history = {
        year: dict(terms) for year, terms in structured_history.items()
    }

    context = {
        'student': student,
        'history': history,
        'term_aggregates': dict(term_aggregates),
        'student_classroom': getattr(student, 'classroom', None),
        'student_stream': getattr(student, 'stream', None),
    }

    return render(request, 'academic/student_history.html', context)