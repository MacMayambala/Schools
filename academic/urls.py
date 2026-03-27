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
]