from django import forms
from .models import Subject
from students.models import Classroom

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'classrooms']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mathematics'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MTC'}),
            'classrooms': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if school:
            # Only show classrooms belonging to THIS school
            self.fields['classrooms'].queryset = Classroom.objects.filter(school=school)