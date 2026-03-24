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