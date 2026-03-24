from django import forms
from .models import Payment

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        # Use the names that match your Model's variables
        fields = ['amount', 'method', 'reference', 'depositor']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount in UGX'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., REC-001'}),
            'depositor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Who brought the money?'}),
        }