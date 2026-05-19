from django import forms
from .models import Student, ClassStream, Classroom, Stream

class BaseTenantForm(forms.ModelForm):
    """
    Base form that automatically filters querysets by school 
    and applies premium styling.
    """
    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        
        # Filter all foreign keys to only show items belonging to this school
        if self.school:
            for field_name, field in self.fields.items():
                if hasattr(field, 'queryset') and hasattr(field.queryset.model, 'school'):
                    field.queryset = field.queryset.filter(school=self.school)
        
        # Add Bootstrap styling to every field
        for field in self.fields.values():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.update({'class': 'form-select rounded-3'})
            else:
                field.widget.attrs.update({'class': 'form-control rounded-3'})

class StudentForm(BaseTenantForm): # Inheriting from BaseTenantForm
    class Meta:
        model = Student
        fields = [
            'photo', 'first_name', 'last_name', 'class_stream', 'studentPaymentCode',
            'section', 'gender', 'date_of_birth', 
            'guardian_name', 'guardian_relation', 'guardian_phone', 
            'guardian_email', 'guardian_address'
        ]
        
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'guardian_address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter residential address...'}),
            'guardian_email': forms.EmailInput(attrs={'placeholder': 'example@gmail.com'}),
            'guardian_phone': forms.TextInput(attrs={'placeholder': 'e.g. 0700 000 000'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.school:
            self.fields['class_stream'].queryset = ClassStream.objects.filter(
                school=self.school, 
                is_active=True
            ).select_related('classroom', 'stream').order_by('classroom__level', 'stream__name')
            
        self.fields['class_stream'].empty_label = "--- Select Class & Stream ---"

class ClassroomForm(BaseTenantForm):
    class Meta:
        model = Classroom
        fields = ['name', 'short_name', 'level']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Primary One'}),
            'short_name': forms.TextInput(attrs={'placeholder': 'e.g. P1'}),
        }

class StreamForm(BaseTenantForm):
    class Meta:
        model = Stream
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. North, Blue, or A'}),
        }

class ClassStreamForm(BaseTenantForm):
    class Meta:
        model = ClassStream
        fields = ['classroom', 'stream', 'class_teacher', 'capacity', 'room_number']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # LAZY IMPORT: Fixes the "academic.Teacher not loaded" error
        try:
            from academic.models import Teacher 
            if self.school:
                self.fields['class_teacher'].queryset = Teacher.objects.filter(school=self.school)
        except ImportError:
            pass

class FeeStructureForm(BaseTenantForm):
    class Meta:
        from finance.models import FeeStructure
        model = FeeStructure
        fields = ['classroom', 'term', 'year', 'section', 'tuition_amount']
        widgets = {
            'tuition_amount': forms.NumberInput(attrs={'placeholder': '0.00'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.school:
            self.fields['classroom'].empty_label = "--- Select Class Level ---"