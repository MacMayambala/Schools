from django.db import models
from core.models import TenantModel
from students.models import Student, Classroom

class FeeCategory(TenantModel):
    """ e.g., Tuition, Uniform, Building Fund """
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Fee Categories"

    def __str__(self):
        return f"{self.name} ({self.school.code})"

class FeeStructure(TenantModel):
    classroom = models.ForeignKey('students.Classroom', on_delete=models.CASCADE)
    term = models.CharField(max_length=1, choices=[('1','1'), ('2','2'), ('3','3')])
    year = models.IntegerField(default=2026)
    amount = models.DecimalField(max_digits=12, decimal_places=2) # e.g., 600,000 for S.1

    def __str__(self):
        return f"{self.classroom.name} - Term {self.term} ({self.amount})"

import datetime
from django.db import models
# Assuming TenantModel is imported from your shared/base apps
import datetime
from django.db import models

class Invoice(TenantModel):
    """ The total bill for a student for a specific term """
    # Points to the Student model in your 'students' app
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='invoices'
    )
    term = models.CharField(max_length=20)
    year = models.IntegerField(default=datetime.date.today().year)
    
    # Financials
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tracking
    # finance/models.py
    
    # finance/models.py (Final version)
    created_at = models.DateField(auto_now_add=True) 
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)

    @property
    def balance(self):
        return self.total_amount - self.paid_amount

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Multi-tenant safe: counts only invoices for THIS school
            count = Invoice.objects.filter(school=self.school).count() + 1
            self.invoice_number = f"INV-{self.year}-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.student.get_full_name()}"

class Payment(TenantModel):
    """ Individual payment transactions """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    date_paid = models.DateField(auto_now_add=True)
    receipt_number = models.CharField(max_length=50, unique=True)
    payment_method = models.CharField(max_length=50, choices=[('Cash', 'Cash'), ('Bank', 'Bank Transfer'), ('Mobile Money', 'Mobile Money')])

    def save(self, *args, **kwargs):
        # Update the invoice paid_amount when a payment is saved
        super().save(*args, **kwargs)
        self.invoice.paid_amount += self.amount_paid
        self.invoice.save()

    def __str__(self):
        return f"Receipt {self.receipt_number} - {self.amount_paid}"
    

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

class Payment(models.Model): # Or TenantModel
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_paid = models.DateTimeField(auto_now_add=True)
    
    # Category Tracking (Chart of Accounts)
    # This links the payment to a specific account (e.g., 'Cash at Hand')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='account_payments', null=True)
    
    # Payment Details
    method = models.CharField(max_length=50, choices=[
        ('Cash', 'Cash'),
        ('Bank', 'Bank Deposit'),
        ('Mobile Money', 'Mobile Money')
    ], default='Cash')
    reference = models.CharField(max_length=100, blank=True, null=True, help_text="Receipt or Bank Slip No.")
    
    # Audit Trail: Who made the transaction?
    # 1. The Person at the counter (Parent/Student)
    depositor = models.CharField(max_length=255, help_text="Name of the person who brought the money")
    
    # 2. The Staff Member logged in (Staff/Bursar)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='recorded_payments'
    )
    
    school = models.ForeignKey('core.School', on_delete=models.CASCADE)

    def __str__(self):
        staff_name = self.recorded_by.username if self.recorded_by else "System"
        return f"UGX {self.amount} by {self.depositor} (Rec: {staff_name})"

    class Meta:
        ordering = ['-date_paid']