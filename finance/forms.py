from django import forms
from .models import Payment
from django import forms
from .models import Payment
from students.models import Classroom

from django import forms
from .models import Payment

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'amount_paid', 
            'payment_method', 
            'depositor',        # Added for "Paid By" in email
            'phone_number', 
            'transaction_id',    # Added for Bank/Momo reference
            'status'
        ]
        widgets = {
            'amount_paid': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '1',
                'placeholder': 'Enter amount'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'depositor': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Name of person paying'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '2567...'
            }),
            'transaction_id': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Bank Slip or MoMo Ref'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set optional fields
        self.fields['phone_number'].required = False
        self.fields['transaction_id'].required = False
        self.fields['depositor'].required = True  # Highly recommended for receipts


        
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
        # 1. REMOVE 'other_requirements_total' from this list
        fields = ['classroom', 'term', 'year', 'section', 'tuition_amount']

    def __init__(self, *args, **kwargs):
        # 2. Pop the 'school' argument so it doesn't break the parent init
        self.school = kwargs.pop('school', None)
        
        super().__init__(*args, **kwargs)

        # 3. Apply Multi-Tenancy filtering and Bootstrap styling
        if self.school:
            self.fields['classroom'].queryset = Classroom.objects.filter(school=self.school)
            
            for field_name, field in self.fields.items():
                # Use form-select for dropdowns, form-control for standard inputs
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select shadow-sm'})
                else:
                    field.widget.attrs.update({'class': 'form-control shadow-sm'})