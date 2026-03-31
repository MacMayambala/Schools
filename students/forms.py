# students/forms.py
from django import forms
from .models import Student, Classroom

from django import forms
from .models import Student, Classroom, Stream

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        # 1. Added 'stream' and 'section' to the fields list
        fields = [
            'photo', 'first_name', 'last_name', 'classroom', 
            'stream', 'section', 'gender', 'date_of_birth', 
            'guardian_name', 'guardian_relation', 'guardian_phone', 
            'guardian_email', 'guardian_address'
        ]
        
        # 2. Refined widgets for a premium UI feel
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'guardian_address': forms.Textarea(attrs={
                'rows': 2, 
                'placeholder': 'Enter residential address...'
            }),
            'guardian_email': forms.EmailInput(attrs={
                'placeholder': 'example@gmail.com'
            }),
            'guardian_phone': forms.TextInput(attrs={
                'placeholder': 'e.g. 0700 000 000'
            }),
        }

    def __init__(self, *args, **kwargs):
        # 3. Pull the 'school' (tenant) from the view
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        
        if school:
            # 4. Filter querysets so SAO doesn't see OLAM's classes or streams
            self.fields['classroom'].queryset = Classroom.objects.filter(school=school)
            self.fields['stream'].queryset = Stream.objects.filter(school=school)
            
        # 5. Clean look: Add 'Select' placeholders to dropdowns
        self.fields['classroom'].empty_label = "--- Select Class ---"
        self.fields['stream'].empty_label = "--- Select Stream (Optional) ---"


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
        # 1. REMOVED 'other_requirements_total' from this list
        fields = [
            'classroom', 'term', 'year', 'section', 
            'tuition_amount'
        ]
        widgets = {
            'classroom': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'term': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'year': forms.NumberInput(attrs={'class': 'form-control rounded-3'}),
            'section': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'tuition_amount': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'placeholder': '0.00'}),
            # 2. REMOVED the widget entry for other_requirements_total
        }

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if school:
            self.fields['classroom'].queryset = Classroom.objects.filter(school=school)