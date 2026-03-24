from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Invoice, FeeStructure
from .services import generate_bulk_invoices
from students.models import Classroom

def finance_dashboard(request):
    """ Overview of total collections vs expectations """
    invoices = Invoice.objects.filter(school=request.school)
    total_expected = sum(i.total_amount for i in invoices)
    total_collected = sum(i.paid_amount for i in invoices)
    
    context = {
        'total_expected': total_expected,
        'total_collected': total_collected,
        'balance': total_expected - total_collected,
        'recent_invoices': invoices.order_by('-id')[:10]
    }
    return render(request, 'finance/dashboard.html', context)

# finance/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Invoice, FeeStructure
from students.models import Student, Classroom

def run_bulk_billing(request):
    if request.method == "POST":
        classroom_id = request.POST.get('classroom')
        term = request.POST.get('term')
        year = request.POST.get('year')
        
        # Get fee structure for this class
        fee_structure = FeeStructure.objects.filter(
            classroom_id=classroom_id, 
            term=term, 
            year=year,
            school=request.school
        ).first()

        if not fee_structure:
            messages.error(request, "No Fee Structure found for this class and term. Please set it in Admin first.")
            return redirect('finance:bulk_bill')

        # Get students in this class
        students = Student.objects.filter(classroom_id=classroom_id, school=request.school, is_active=True)
        count = 0
        
        for student in students:
            # Only create if invoice doesn't exist
            _, created = Invoice.objects.get_or_create(
                student=student,
                term=term,
                year=year,
                school=request.school,
                defaults={'total_amount': fee_structure.amount}
            )
            if created:
                count += 1
        
        messages.success(request, f"Successfully generated {count} new invoices.")
        return redirect('finance:dashboard')

    classrooms = Classroom.objects.filter(school=request.school)
    return render(request, 'finance/bulk_bill.html', {'classrooms': classrooms})

from django.shortcuts import render, redirect, get_object_or_404
from .models import Invoice, Payment
from .forms import PaymentForm

def record_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, school=request.school)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.school = request.school
            payment.save()
            messages.success(request, f"Payment of {payment.amount_paid} recorded for {invoice.student}")
            return redirect('finance:receipt_detail', payment_id=payment.id)
    else:
        # Suggest the remaining balance as the default payment amount
        form = PaymentForm(initial={'amount_paid': invoice.balance})
        
    return render(request, 'finance/record_payment.html', {'form': form, 'invoice': invoice})

def receipt_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, school=request.school)
    return render(request, 'finance/receipt.html', {'payment': payment})



from django.db.models import F, Sum
from django.shortcuts import render
from .models import Invoice

def defaulters_report(request):
    school = request.school
    classroom_id = request.GET.get('classroom')
    
    # Get all invoices where the balance is greater than zero
    # Formula: total_amount - paid_amount > 0
    defaulters = Invoice.objects.filter(
        school=school,
        total_amount__gt=F('paid_amount')
    ).select_related('student', 'student__classroom')

    if classroom_id:
        defaulters = defaulters.filter(student__classroom_id=classroom_id)

    # Calculate total debt for the school summary
    total_debt = defaulters.aggregate(Sum('total_amount'), Sum('paid_amount'))
    expected = total_debt['total_amount__sum'] or 0
    paid = total_debt['paid_amount__sum'] or 0
    actual_balance = expected - paid

    context = {
        'defaulters': defaulters,
        'actual_balance': actual_balance,
        'classrooms': Classroom.objects.filter(school=school)
    }
    return render(request, 'finance/defaulters_list.html', context)


# finance/views.py
from decimal import Decimal  # Add this import at the top

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.db import transaction  # Crucial for financial safety
from decimal import Decimal
from .models import Invoice, Payment, Account

from decimal import Decimal
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Invoice, Payment, Account

def record_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, school=request.school)
    
    if request.method == "POST":
        try:
            with transaction.atomic():
                amount = Decimal(request.POST.get('amount'))
                account_id = request.POST.get('account')
                target_account = get_object_or_404(Account, id=account_id, school=request.school)

                # 1. Create the payment record
                Payment.objects.create(
                    invoice=invoice,
                    amount=amount,
                    account=target_account,
                    method=request.POST.get('method'),
                    reference=request.POST.get('reference'),
                    depositor=request.POST.get('depositor'),
                    recorded_by=request.user,
                    school=request.school,
                )

                # 2. Update the School Account (Increase Cash/Bank)
                target_account.balance += amount
                target_account.save()

                # 3. Update the Invoice (Decrease student's debt)
                invoice.paid_amount += amount
                invoice.save()

            messages.success(request, f"Successfully recorded UGX {amount:,.0f} for {invoice.student.first_name}.")
            return redirect('finance:dashboard')

        except Exception as e:
            messages.error(request, f"Error processing payment: {str(e)}")
            return redirect('finance:record_payment', invoice_id=invoice.id)

    # We use __iexact to handle "Asset", "asset", or "ASSET"
    # We also order them by name so they are easy to find
    accounts = Account.objects.filter(
        school=request.school, 
        account_type__iexact='Asset'
    ).order_by('name')

    return render(request, 'finance/record_payment.html', {
        'invoice': invoice,
        'accounts': accounts
    })


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Account

def account_list(request):
    """ View to manage the Chart of Accounts """
    accounts = Account.objects.filter(school=request.school).order_by('account_type', 'code')
    
    if request.method == "POST":
        name = request.POST.get('name')
        code = request.POST.get('code')
        acc_type = request.POST.get('account_type')
        opening_balance = request.POST.get('opening_balance', 0)

        # Create the account tied to this school
        Account.objects.create(
            school=request.school,
            name=name,
            code=code,
            account_type=acc_type,
            balance=opening_balance
        )
        messages.success(request, f"Account '{name}' created successfully.")
        return redirect('finance:account_list')

    return render(request, 'finance/account_list.html', {'accounts': accounts})




from django.utils import timezone
from django.db.models import Sum
from django.utils import timezone
from django.db.models import Sum

from django.utils import timezone

from django.utils import timezone
from django.db.models import Sum
from datetime import datetime

from django.db.models import Sum, F

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from .models import Payment
# Ensure you have these imports if not already there

def daily_collection_report(request):
    # 1. Capture Date Filters from the URL
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    # Default to today (Uganda Local Time) if no dates are provided
    today = timezone.localtime(timezone.now()).date()
    start_date = start_date_str if start_date_str else today
    end_date = end_date_str if end_date_str else today

    # 2. Fetch Payments with related Student and Invoice data
    # We use select_related to get parent_phone and classroom name efficiently
    payments = Payment.objects.filter(
        school=request.school,
        date_paid__date__range=[start_date, end_date]
    ).select_related(
        'invoice__student', 
        'invoice__student__classroom', 
        'account',
        'recorded_by'
    ).order_by('-date_paid', '-id')

    # 3. Calculate Totals for the selected period
    total_collected = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # 4. Create the Summary Breakdown by Payment Method
    summary_by_method = payments.values('method').annotate(total=Sum('amount'))

    return render(request, 'finance/daily_report.html', {
        'payments': payments,
        'total_collected': total_collected,
        'summary_by_method': summary_by_method,
        'start_date': start_date,
        'end_date': end_date,
        'today': today,
    })
import openpyxl
from django.http import HttpResponse
from django.utils import timezone
from .models import Payment

def export_collections_excel(request):
    # 1. Get dates from the request (matching the report view)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # 2. Fetch the same data as the report
    payments = Payment.objects.filter(
        school=request.school,
        date_paid__date__range=[start_date, end_date]
    ).select_related(
        'invoice__student', 
        'invoice__student__classroom', 
        'account'
    ).order_by('-date_paid')

    # 3. Create Excel Workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Collection_Report"

    # 4. Define Headers (Including the new columns)
    headers = [
        'Date', 
        'Student Name', 
        'Admission No.', 
        'Class', 
        'Parent Phone', 
        'Method', 
        'Account', 
        'Amount Paid (UGX)', 
        'Remaining Balance (UGX)'
    ]
    ws.append(headers)

    # 5. Add Data Rows
    for p in payments:
        ws.append([
            p.date_paid.strftime('%d/%m/%Y'),
            p.invoice.student.get_full_name(),
            p.invoice.student.admission_number,
            p.invoice.student.classroom.name if p.invoice.student.classroom else "N/A",
            p.invoice.student.guardian_phone or "No Contact",
            p.method,
            p.account.name if p.account else "No Account",  # Add this check here
            p.amount,
            p.invoice.balance  # This pulls the current balance from the invoice
        ])

    # 6. Formatting: Make headers bold
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True)

    # 7. Generate Response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"Collections_{start_date}_to_{end_date}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    wb.save(response)
    return response
from django.db.models import Q

from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from .models import Invoice, Payment

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Student, Invoice, Payment

def student_statement(request, student_id):
    # Ensure student belongs to this school
    student = get_object_or_404(Student, id=student_id, school=request.school)
    
    # 1. Fetch Invoices and Payments
    invoices = Invoice.objects.filter(student=student, school=request.school)
    payments = Payment.objects.filter(invoice__student=student, school=request.school)

    ledger = []

    # 2. Build the Ledger from Invoices (Debits)
    for inv in invoices:
        ledger.append({
            # Using getattr as a safety net in case migrations aren't finished
            'date': getattr(inv, 'created_at', timezone.now().date()), 
            'description': f"Fees Invoice - {inv.term} {inv.year}",
            'debit': inv.total_amount,
            'credit': 0,
        })
    
    # 3. Build the Ledger from Payments (Credits)
    for pay in payments:
        # Ensuring we use a date object for sorting
        p_date = pay.date_paid.date() if hasattr(pay.date_paid, 'date') else pay.date_paid
        ledger.append({
            'date': p_date,
            'description': f"Fee Payment - {pay.method} ({pay.reference or 'No Ref'})",
            'debit': 0,
            'credit': pay.amount,
        })

    # 4. Sort everything by date
    # This is critical so that payments appear after the invoices they pay for
    ledger.sort(key=lambda x: x['date'])

    # 5. Calculate Running Balance
    running_total = 0
    for entry in ledger:
        running_total += (entry['debit'] - entry['credit'])
        entry['running_balance'] = running_total

    return render(request, 'finance/student_statement.html', {
        'student': student,
        'ledger': ledger,
        'final_balance': running_total,
        'today': timezone.now().date(),
    })