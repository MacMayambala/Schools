from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.StudentListView.as_view(), name='student_list'),
    path('add/', views.StudentCreateView.as_view(), name='student_add'),
    path('bulk-import/', views.bulk_import_students, name='bulk_import'),
    path('<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_edit'),
    path('import/template/', views.download_student_import_template, name='download_template'),
    path('bulk-action/', views.student_bulk_action, name='bulk_action'), # Add this line
    path('edit/<int:pk>/', views.StudentUpdateView.as_view(), name='student_update'),
    path('bulk-action/', views.student_bulk_action, name='bulk_action')
]