from django import forms
from .models import Payment
from django import forms
from .models import Payment

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        # Updated these fields to match the new Model names
        fields = [
            'amount_paid', 
            'payment_method', 
            'phone_number', 
            'status'
        ]
        widgets = {
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2567...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure only Mobile Money requires a phone number
        self.fields['phone_number'].required = False

from django import forms
from .models import FeeStructure, FeeCategory
from students.forms import BaseTenantForm # Import the base you just made

from django import forms
from .models import FeeStructure

from django import forms
from .models import FeeStructure

class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['classroom', 'term', 'year', 'tuition_amount', 'other_requirements_total']

    def __init__(self, *args, **kwargs):
        # 1. Pop the 'school' argument out of kwargs so the parent class doesn't see it
        self.school = kwargs.pop('school', None)
        
        # 2. Call the original __init__
        super().__init__(*args, **kwargs)

        # 3. Use the school to filter the classroom choices
        if self.school:
            self.fields['classroom'].queryset = self.fields['classroom'].queryset.filter(school=self.school)
            
            # Add Bootstrap styling to all fields
            for field in self.fields.values():
                field.widget.attrs.update({'class': 'form-control'})