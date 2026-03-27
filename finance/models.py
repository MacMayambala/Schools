from django.db import models
from core.models import TenantModel
from students.models import Student, Classroom

from django.db import models
from core.models import TenantModel




class FeeCategory(TenantModel):
    """ e.g., Tuition, Uniform, Building Fund, Medical """
    name = models.CharField(max_length=100)
    is_mandatory = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Fee Categories"

    def __str__(self):
        return self.name

class FeeStructure(TenantModel):
    SECTION_CHOICES = [('Day', 'Day'), ('Boarding', 'Boarding')]
    
    classroom = models.ForeignKey('students.Classroom', on_delete=models.CASCADE)
    term = models.CharField(max_length=1, choices=[('1','1'), ('2','2'), ('3','3')])
    year = models.IntegerField(default=2026)
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default='Day')
    
    # Base Tuition for this specific class/section
    tuition_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Requirements (Uniforms, etc.) are often class-specific
    other_requirements_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0, 
        help_text="Total for Uniforms, Sch. Dev, etc."
    )

    @property
    def total_fees(self):
        return self.tuition_amount + self.other_requirements_total

    def __str__(self):
        return f"{self.classroom.short_name} ({self.section}) - Term {self.term}"
import datetime
from django.db import models
# Assuming TenantModel is imported from your shared/base apps
import datetime
from django.db import models

import uuid
from django.db import models
from django.db.models import Sum
from core.models import TenantModel

import datetime
from django.db import models, transaction
from django.db.models import Sum
from core.models import TenantModel

class Invoice(TenantModel):
    """ The total bill for a student for a specific term """
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='invoices')
    term = models.CharField(max_length=20)
    year = models.IntegerField(default=datetime.date.today().year)
    
    # Financials
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateField(auto_now_add=True) 
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)

    @property
    def balance(self):
        return self.total_amount - self.paid_amount

    def update_totals(self):
        """Recalculate paid_amount based only on Completed payments"""
        # Summing from the Payment model's amount_paid field
        total = self.payments.filter(status='Completed').aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        self.paid_amount = total
        # Using update to avoid re-triggering the save() logic unnecessarily
        Invoice.objects.filter(pk=self.pk).update(paid_amount=total)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Start with the current count + 1
            year_prefix = self.year
            base_count = Invoice.objects.filter(school=self.school, year=year_prefix).count() + 1
            
            # Loop until we find a number that isn't taken
            while True:
                candidate = f"INV-{year_prefix}-{base_count:04d}"
                if not Invoice.objects.filter(invoice_number=candidate).exists():
                    self.invoice_number = candidate
                    break
                base_count += 1
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.student.get_full_name()}"
    

class FeeLineItem(TenantModel):
    """ Individual components of a FeeStructure """
    structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(FeeCategory, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.category.name}: {self.amount}"

# Update your FeeStructure total_fees property to sum these up automatically
# (Add this to your existing FeeStructure model)
    @property
    def calculated_requirements(self):
        return sum(item.amount for item in self.items.all())

    @property
    def total_fees(self):
        return self.tuition_amount + self.calculated_requirements

import uuid
from django.db import models
from core.models import TenantModel # Ensure this path is correct for your project

import uuid
from django.db import models
from core.models import TenantModel
import uuid
from django.db import models
from core.models import TenantModel

import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from core.models import TenantModel  # Assuming TenantModel is in your core app
import uuid
from django.db import models
from django.conf import settings
from core.models import TenantModel

class Payment(TenantModel):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('Bank', 'Bank Transfer'),
        ('Mobile Money', 'Mobile Money'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]

    # Relationships
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='payments')
    account = models.ForeignKey('Account', on_delete=models.PROTECT, related_name='payments', null=True)
    
    # Financials
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    date_paid = models.DateTimeField(auto_now_add=True)
    receipt_number = models.CharField(max_length=50, editable=False, unique=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Completed')
    
    # Audit Tracking (The missing fields)
    depositor = models.CharField(max_length=100, blank=True, null=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # IDs
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            while True:
                new_receipt = f"RCT-{uuid.uuid4().hex[:10].upper()}"
                if not Payment.objects.filter(receipt_number=new_receipt).exists():
                    self.receipt_number = new_receipt
                    break
        
        super().save(*args, **kwargs)
        
        # Sync with invoice
        if self.status == 'Completed' and self.invoice:
            self.invoice.update_totals()

    def __str__(self):
        return f"{self.receipt_number} - {self.amount_paid}"

from django.db import models
from django.conf import settings
from decimal import Decimal

# Assuming TenantModel is defined in your core/shared app
# If not, use models.Model
# from core.models import TenantModel 

class Account(models.Model): # Or TenantModel
    ACCOUNT_TYPES = [
        ('Asset', 'Asset (e.g., Cash, Bank)'),
        ('Liability', 'Liability (e.g., Loans)'),
        ('Equity', 'Equity'),
        ('Income', 'Income (e.g., Fees)'),
        ('Expense', 'Expense (e.g., Salaries)'),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    school = models.ForeignKey('core.School', on_delete=models.CASCADE) # For multi-tenant

    def __str__(self):
        return f"{self.code} - {self.name} ({self.account_type})"



