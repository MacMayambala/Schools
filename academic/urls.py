# academic/urls.py
from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    # ADD THIS: A landing page to see all academic records/classes
    path('', views.academic_dashboard, name='dashboard'), 
    
    path('marks/enter/<int:classroom_id>/<int:subject_id>/', views.enter_marks, name='enter_marks'),
    path('report/<int:student_id>/<str:term>/<int:year>/', views.student_report_card, name='report_card'),
    path('subjects/', views.manage_subjects, name='manage_subjects'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teachers/directory/', views.teacher_directory, name='teacher_directory'),
    path('requirements/create/', views.create_requirement, name='create_requirement'),
    path('teacher/<int:pk>/edit/', views.teacher_edit, name='teacher_edit'),
    path('teacher/<int:pk>/status/', views.teacher_status_toggle, name='teacher_status_toggle'),
    path('teacher/<int:teacher_id>/assign/', views.update_teacher_assignments, name='update_assignments'),
    path('teacher/add/', views.add_teacher, name='add_teacher'),
    path('student/<int:student_id>/history/', views.student_report_history, name='student_history'),
    #path('teacher/<int:pk>/report/', views.teacher_performance_report, name='teacher_performance_report'),
    #path('report/<int:student_id>/<str:term>/<str:year>/', views.student_report_card,name='student_report_card'),
    # The main interface page
    
]
