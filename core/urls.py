from django.urls import path, reverse_lazy
from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
from .forms import SchoolLoginForm
from .views import SchoolLoginView
from .views import logout_view

app_name = 'core'

urlpatterns = [
    #path('', views.index, name='index'), # This is your main dashboard
    
    # Using your custom class-based view
    path('auth/login/', SchoolLoginView.as_view(), name='login'),
    
    # Using your custom function-based logout
    path('auth/logout/', logout_view, name='logout'),
    # 1. Submit email form
    path('password-reset/', views.MyPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.MyPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.MyPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', views.MyPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('', views.dashboard_view, name='index'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/unlock/', views.unlock_user, name='unlock_user'),
    
    # Audit Trail
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    
    # Optional: API endpoint if you want to load chart data via AJAX later
    #path('api/chart-data/', views.chart_data_api, name='chart_data_api'),
    path('manage-access/', views.assign_rights, name='assign_rights'),
    
    # The action endpoint for the form
    path('manage-access/update/<int:user_id>/', views.update_user_rights, name='update_rights'),
    path('roles/', views.group_list, name='group_list'),
    path('roles/create/', views.create_group, name='create_group'),
    path('roles/edit/<int:group_id>/', views.edit_group, name='edit_group'),
             
 ]


