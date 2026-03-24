from django.urls import path
from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
from .forms import SchoolLoginForm

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'), # This is your main dashboard
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=SchoolLoginForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]