# students/forms.py
from django import forms
from .models import Student, Classroom

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        # List ALL the fields you want to show in the form
        fields = [
            'photo', 'first_name', 'last_name', 'classroom', 
            'gender', 'date_of_birth', 'guardian_name', 
            'guardian_relation', 'guardian_phone', 
            'guardian_email', 'guardian_address'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'guardian_address': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        # This part ensures the student can only be put in a classroom 
        # that belongs to the logged-in school
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if school:
            self.fields['classroom'].queryset = Classroom.objects.filter(school=school)


from django import forms
from .models import Classroom

class BaseTenantForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        # Filter all foreign keys to only show items belonging to this school
        for field_name, field in self.fields.items():
            if hasattr(field, 'queryset'):
                field.queryset = field.queryset.filter(school=self.school)
        
        # Add Bootstrap styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control rounded-3'})

from django import forms
from .models import Classroom, Stream

class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        # We exclude 'school' because it's handled automatically in the view
        fields = ['name', 'short_name', 'level']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Primary One'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. P.1'}),
            'level': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class StreamForm(forms.ModelForm):
    class Meta:
        model = Stream
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. North, Blue, or A'}),
        }


from django import forms
from finance.models import FeeStructure
from students.models import Classroom

class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = [
            'classroom', 'term', 'year', 'section', 
            'tuition_amount', 'other_requirements_total'
        ]
        widgets = {
            'classroom': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'term': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'year': forms.NumberInput(attrs={'class': 'form-control rounded-3'}),
            'section': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'tuition_amount': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'placeholder': '0.00'}),
            'other_requirements_total': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'placeholder': '0.00'}),
        }

    def __init__(self, *args, **kwargs):
        # Extract school to filter the classroom dropdown
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if school:
            self.fields['classroom'].queryset = Classroom.objects.filter(school=school)