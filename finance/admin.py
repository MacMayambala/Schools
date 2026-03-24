from django.contrib import admin
from .models import FeeCategory, FeeStructure, Invoice, Payment

@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'school')

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    # Change 'category' to 'classroom' (or whatever fields exist in your model)
    list_display = ('classroom', 'amount', 'term', 'year', 'school') 
    list_filter = ('classroom', 'term', 'year', 'school')
    search_fields = ('classroom__name',)
from django.contrib import admin
from .models import Invoice, Payment

class PaymentInline(admin.TabularInline):
    """ Allows viewing payments directly inside the Invoice page """
    model = Payment
    extra = 0  # Prevents showing empty rows by default
    readonly_fields = ('date_paid', 'recorded_by', 'amount', 'method', 'reference')
    can_delete = False  # Safety: Prevent accidental deletion of payment records from the invoice page
    
    def has_add_permission(self, request, obj=None):
        return False # Payments should usually be added through the Payment form/view

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    # Attach the inline here
    inlines = [PaymentInline]
    
    list_display = ('invoice_number', 'student', 'term', 'year', 'total_amount', 'paid_amount', 'balance_status', 'created_at')
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
        from django.utils.html import format_html
        balance = obj.balance
        
        if balance <= 0:
            return format_html('<span style="color: #198754; font-weight: bold;">[CLEARED]</span>')
        
        # Format the number first, then pass it to format_html
        formatted_balance = f"{balance:,.0f}"
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">UGX {}</span>', 
            formatted_balance
        )
# Also register Payment separately so it has its own menu item
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'method', 'date_paid', 'recorded_by')
    list_filter = ('method', 'date_paid')
    search_fields = ('invoice__invoice_number', 'invoice__student__first_name', 'reference')