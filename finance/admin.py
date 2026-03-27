from django.contrib import admin
from django.utils.html import format_html
from .models import FeeCategory, FeeStructure, Invoice, Payment

# 1. Fee Category Admin
@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'school')
    list_filter = ('school',)

# 2. Fee Structure Admin
@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = (
        'classroom', 
        'section', 
        'term', 
        'year', 
        'tuition_amount', 
        'other_requirements_total', 
        'total_fees_display'
    )
    list_filter = ('classroom', 'term', 'year', 'section', 'school')
    search_fields = ('classroom__name',)

    @admin.display(description='Total (UGX)')
    def total_fees_display(self, obj):
        return f"UGX {obj.total_fees:,.0f}"

# 3. Payment Inline (for Invoice view)
class PaymentInline(admin.TabularInline):
    """ Allows viewing payments directly inside the Invoice page """
    model = Payment
    extra = 0
    # Updated to match our MoMo-enabled model fields
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
        balance = obj.balance
        if balance <= 0:
            return format_html('<span style="color: #198754; font-weight: bold;">[CLEARED]</span>')
        
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">UGX {:,.0f}</span>', 
            balance
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