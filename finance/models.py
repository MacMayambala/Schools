import uuid
from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from django.db.models import Sum
from django.conf import settings
from core.models import TenantModel   # Your multi-tenant base model

import uuid
from decimal import Decimal
from django.db import models, transaction
from django.db.models import Sum
from core.models import TenantModel 
import uuid
from decimal import Decimal
from django.db import models
from django.db.models import Sum
from core.models import TenantModel 

from decimal import Decimal
from django.db import models
from django.db.models import Sum
from core.models import TenantModel 

class FeeCategory(TenantModel):
    name = models.CharField(max_length=100)
    is_mandatory = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Fee Categories"

    def __str__(self):
        return self.name

class FeeStructure(TenantModel):
    SECTION_CHOICES = [('Day', 'Day'), ('Boarding', 'Boarding')]
    TERM_CHOICES = [
        ('1', 'Term 1'),
        ('2', 'Term 2'),
        ('3', 'Term 3'),
    ]
    term = models.CharField(max_length=1, choices=TERM_CHOICES, db_index=True)
    classroom = models.ForeignKey('students.Classroom', on_delete=models.CASCADE)
    year = models.IntegerField(default=2026)
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default='Day')
    tuition_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def total_fees(self):
        # Must match 'template_items' in FeeStructureItem
        additional = self.template_items.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return self.tuition_amount + additional

    def __str__(self):
        return f"{self.classroom.short_name} ({self.section}) - Term {self.term} {self.year}"

class FeeStructureItem(TenantModel):
    """The Template/Blueprint items for a structure"""
    fee_structure = models.ForeignKey(
        FeeStructure, 
        related_name='template_items',  # <--- Use this name in prefetch_related
        on_delete=models.CASCADE
    )
    category = models.ForeignKey(FeeCategory, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

class FeeItem(TenantModel):
    """The items used for actual student billing"""
    structure = models.ForeignKey(
        FeeStructure, 
        on_delete=models.CASCADE,
        related_name='billed_items' 
    )
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)


from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.db.models import Sum
from core.models import TenantModel


class Invoice(TenantModel):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='invoices')
    term = models.CharField(max_length=20)
    year = models.IntegerField(default=timezone.now().year)

    # Breakdown
    current_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    previous_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Stored totals
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'term', 'year', 'school')
        ordering = ['-year', '-term', '-created_at']

    @property
    def balance(self):
        """Always return the correct remaining balance"""
        return self.total_amount - self.paid_amount

    def sync_paid_amount(self):
        """Recalculate paid_amount from actual payments - this is the source of truth"""
        total_paid = self.payments.filter(status='Completed').aggregate(
            total=Sum('amount_paid')
        )['total'] or Decimal('0.00')

        # Update without triggering save() again
        Invoice.objects.filter(pk=self.pk).update(paid_amount=total_paid)
        self.paid_amount = total_paid  # Update in-memory object too
        return total_paid

    def save(self, *args, **kwargs):
        # 1. Always recalculate total_amount from current_fees + previous_balance
        self.total_amount = (self.current_fees or Decimal('0')) + (self.previous_balance or Decimal('0'))

        # 2. Generate invoice number if new
        if not self.invoice_number:
            base_count = Invoice.objects.filter(
                school=self.school, year=self.year
            ).count() + 1
            while True:
                candidate = f"INV-{self.year}-{base_count:04d}"
                if not Invoice.objects.filter(invoice_number=candidate, school=self.school).exists():
                    self.invoice_number = candidate
                    break
                base_count += 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.student.get_full_name() if self.student else 'No Student'}"
    
class FeeLineItem(TenantModel):
    """Actual billed line items on an invoice (from FeeStructure)"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='invoice_items')
    category = models.ForeignKey(FeeCategory, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('invoice', 'category')   # Prevent duplicate categories per invoice

    def __str__(self):
        return f"{self.category.name}: {self.amount}"


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

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    account = models.ForeignKey('Account', on_delete=models.PROTECT, related_name='payments', null=True, blank=True)

    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    date_paid = models.DateTimeField(auto_now_add=True)
    receipt_number = models.CharField(max_length=50, editable=False, unique=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Completed')

    depositor = models.CharField(max_length=100, blank=True, null=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            while True:
                new_receipt = f"RCT-{uuid.uuid4().hex[:10].upper()}"
                if not Payment.objects.filter(receipt_number=new_receipt).exists():
                    self.receipt_number = new_receipt
                    break

        if not self.transaction_id:
            self.transaction_id = f"TX-{uuid.uuid4().hex[:12].upper()}"

        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.invoice and self.status == 'Completed':
                self.invoice.sync_paid_amount()

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        super().delete(*args, **kwargs)
        if invoice:
            invoice.sync_paid_amount()

    def __str__(self):
        return f"{self.receipt_number} - {self.amount_paid}"


# ==================== CHART OF ACCOUNTS & DOUBLE ENTRY ====================

class Account(TenantModel):
    ACCOUNT_TYPES = [
        ('Asset', 'Asset'),
        ('Liability', 'Liability'),
        ('Equity', 'Equity'),
        ('Income', 'Income'),
        ('Expense', 'Expense'),
    ]

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name} ({self.account_type})"


class JournalEntry(TenantModel):
    date = models.DateField(default=timezone.now)
    reference = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"JE-{self.id} - {self.date}"


class JournalItem(TenantModel):
    journal = models.ForeignKey(JournalEntry, related_name='items', on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    description = models.CharField(max_length=255, blank=True)

    def clean(self):
        if self.debit and self.credit:
            raise ValidationError("Cannot have both debit and credit on the same line.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Do NOT update balance here — do it only when the full JournalEntry is posted


# SMS related models (kept as-is, minor cleanup)
class SMSConfig(models.Model):
    school = models.OneToOneField('core.School', on_delete=models.CASCADE, related_name='sms_config')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cost_per_sms = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school.name} - Balance: {self.balance}"

    @property
    def remaining_messages(self):
        """Number of SMS messages left based on current balance"""
        if self.balance > 0:
            return int(self.balance // self.cost_per_sms)
        return 0


class SMSTransaction(models.Model):
    school = models.ForeignKey('core.School', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=[('TOPUP', 'Top Up'), ('DEBIT', 'SMS Sent')])
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.school.name} - {self.amount} ({self.transaction_type})"