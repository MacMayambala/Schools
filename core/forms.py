from django import forms
from django.contrib.auth.forms import AuthenticationForm

class SchoolLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'placeholder': 'Username',
        'autofocus': True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg',
        'placeholder': 'Password',
    }))



# core/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import CustomUser, Role


from django import forms
from django.contrib.auth.models import User
from .models import Role

class UserCreationForm(forms.ModelForm):
    # Password field is defined explicitly to use the PasswordInput widget
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        }),
        help_text="Choose a strong temporary password."
    )
    
    role = forms.ModelChoiceField(
        queryset=Role.objects.none(), 
        required=True,
        empty_label="Select an Access Role",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        
        # 1. Filter roles by school
        if self.school:
            self.fields['role'].queryset = Role.objects.filter(school=self.school)

        # 2. Add Bootstrap 'form-control' class and placeholders to all fields dynamically
        placeholders = {
            'username': 'e.g. staff.name',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'email@school.com'
        }

        for field_name, field in self.fields.items():
            # Apply common classes
            field.widget.attrs.update({
                'class': 'form-control' if field_name != 'role' else 'form-select',
            })
            # Apply placeholders
            if field_name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[field_name]