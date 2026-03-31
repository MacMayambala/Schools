from django.urls import path, reverse_lazy
from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
from .forms import SchoolLoginForm
from .views import SchoolLoginView
from .views import logout_view

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'), # This is your main dashboard
    
    # Using your custom class-based view
    path('auth/login/', SchoolLoginView.as_view(), name='login'),
    
    # Using your custom function-based logout
    path('auth/logout/', logout_view, name='logout'),
    # 1. Submit email form
    path('password-reset/', views.MyPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.MyPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.MyPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', views.MyPasswordResetCompleteView.as_view(), name='password_reset_complete'),
             
 ]


