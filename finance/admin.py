from django.contrib import admin
from django.utils.html import format_html
from .models import FeeCategory, FeeStructure, Invoice, Payment

from django.contrib import admin
from .models import FeeCategory, FeeStructure, FeeItem, Payment

# 1. Fee Item Inline (The new dynamic breakdown)
class FeeItemInline(admin.TabularInline):
    model = FeeItem
    extra = 1
    fields = ('category', 'amount')

# 2. Fee Category Admin
@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'is_mandatory')
    list_filter = ('school', 'is_mandatory')
    search_fields = ('name',)

# 3. Fee Structure Admin
@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    # Removed 'other_requirements_total' as it no longer exists in the model
    list_display = (
        'classroom', 
        'section', 
        'term', 
        'year', 
        'tuition_amount', 
        'total_fees_display'
    )
    list_filter = ('school', 'classroom', 'term', 'year', 'section')
    search_fields = ('classroom__name',)
    inlines = [FeeItemInline]  # Allows adding requirements directly here

    @admin.display(description='Total (UGX)')
    def total_fees_display(self, obj):
        # This calls the @property we defined in the model
        return f"UGX {obj.total_fees:,.0f}"

# 4. Payment Inline (for Invoice view)
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    # Adjusted to standard payment fields
    readonly_fields = ('receipt_number', 'amount_paid', 'payment_method', 'status', 'date_paid')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False
# 4. Invoice Admin
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [PaymentInline]
    list_display = (
        'invoice_number', 
        'student', 
        'term', 
        'year', 
        'total_amount', 
        'paid_amount', 
        'balance_status', 
        'created_at'
    )
    list_filter = ('term', 'year', 'school')
    search_fields = ('invoice_number', 'student__first_name', 'student__last_name', 'student__admission_number')
    readonly_fields = ('invoice_number', 'created_at', 'paid_amount', 'balance_status')
    
    fieldsets = (
        ('Billing Details', {
            'fields': ('invoice_number', 'student', 'term', 'year')
        }),
        ('Financial Summary', {
            'fields': ('total_amount', 'paid_amount', 'balance_status'),
        }),
        ('System Info', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Balance Status')
    def balance_status(self, obj):
        # 1. Get the raw balance number
        balance = float(obj.balance or 0)
        
        # 2. Logic for Cleared status
        if balance <= 0:
            return format_html('<span style="color: #198754; font-weight: bold;">[CLEARED]</span>')
        
        # 3. Use a regular f-string for the number formatting FIRST, 
        # then wrap it in format_html.
        formatted_balance = f"UGX {balance:,.0f}"
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">{}</span>', 
            formatted_balance
        )

# 5. Payment Admin (Standalone view)
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'receipt_number', 
        'invoice', 
        'amount_paid', 
        'payment_method', 
        'status', 
        'date_paid'
    )
    list_filter = ('payment_method', 'status', 'date_paid', 'school')
    search_fields = ('receipt_number', 'invoice__invoice_number', 'invoice__student__first_name', 'transaction_id')
    readonly_fields = ('receipt_number', 'date_paid')


from django.contrib import admin
from .models import SMSConfig, SMSTransaction

# finance/admin.py

@admin.register(SMSConfig)
class SMSConfigAdmin(admin.ModelAdmin):
    # What columns to show in the list view
    list_display = ('school', 'balance', 'cost_per_sms', 'last_updated')
    search_fields = ('school__name',)
    
    # Notice the (self, obj) here - 'obj' is the specific SMSConfig record
    def last_updated(self, obj):
        # Change 'updated_at' to whatever date field you have in your SMSConfig model
        # If you don't have an updated_at field yet, use 'obj.id' just to test
        return obj.updated_at if hasattr(obj, 'updated_at') else "No record"
    
    last_updated.short_description = "Last Top-up"

# finance/admin.py
from django.contrib import admin
from .models import SMSTransaction

@admin.register(SMSTransaction)
class SMSTransactionAdmin(admin.ModelAdmin):
    list_display = ('school', 'transaction_type', 'amount', 'created_at', 'performed_by')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('school__name', 'description')
    ordering = ('-created_at',)

    def get_readonly_fields(self, request, obj=None):
        """
        If we are editing an existing transaction (obj is not None), 
        make everything read-only to protect the audit trail.
        If we are creating a new one, let us fill in the details.
        """
        if obj: # This is an existing record
            return ('school', 'amount', 'transaction_type', 'description', 'created_at', 'performed_by')
        return ('created_at', 'performed_by') # Only system-generated fields are read-only during creation

    def save_model(self, request, obj, form, change):
        """
        Automatically set the 'performed_by' field to the logged-in admin.
        """
        if not change: # If this is a new record
            obj.performed_by = request.user
        super().save_model(request, obj, form, change)