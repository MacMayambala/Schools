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

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import FeeStructure, Invoice
from students.models import Student, Classroom

def run_bulk_billing(request):
    if request.method == "POST":
        classroom_id = request.POST.get('classroom')
        term = request.POST.get('term')
        year = request.POST.get('year')
        
        # 1. Fetch ALL structures for this class (Day AND Boarding)
        # We use a dictionary for fast lookup: {'Day': 600000, 'Boarding': 950000}
        structures = FeeStructure.objects.filter(
            classroom_id=classroom_id, 
            term=term, 
            year=year,
            school=request.school
        )

        if not structures.exists():
            messages.error(request, "No Fee Structures found for this class. Please set Day/Boarding rates first.")
            return redirect('finance:settings_hub')

        # Map the totals by section
        fee_map = {fs.section: fs.total_fees for fs in structures}

        # 2. Get students in this class
        students = Student.objects.filter(
            classroom_id=classroom_id, 
            school=request.school, 
            is_active=True
        )
        
        count = 0
        skipped = 0

        for student in students:
            # 3. Get the correct amount based on student's section
            amount_to_charge = fee_map.get(student.section)

            if amount_to_charge:
                _, created = Invoice.objects.get_or_create(
                    student=student,
                    term=term,
                    year=year,
                    school=request.school,
                    defaults={'total_amount': amount_to_charge}
                )
                if created:
                    count += 1
            else:
                # This happens if a student is Boarding but you only set a Day fee
                skipped += 1
        
        if count > 0:
            messages.success(request, f"Generated {count} invoices. {skipped} students skipped (missing section fee).")
        else:
            messages.warning(request, "No new invoices were created. They might already exist.")
            
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
                # 1. Map incoming POST data to local variables
                amount_val = Decimal(request.POST.get('amount'))
                target_account = get_object_or_404(Account, id=request.POST.get('account'), school=request.school)

                # 2. Create the payment using the CORRECT field names
                Payment.objects.create(
                    school=request.school,
                    invoice=invoice,
                    amount_paid=amount_val,         # Maps 'amount' -> 'amount_paid'
                    payment_method=request.POST.get('method'), # Maps 'method' -> 'payment_method'
                    transaction_id=request.POST.get('reference'), # Maps 'reference' -> 'transaction_id'
                    depositor=request.POST.get('depositor'),
                    recorded_by=request.user,
                    status='Completed'
                )

                # 3. Financial Updates
                target_account.balance += amount_val
                target_account.save()

                # 4. Update the Invoice Balance
                # Note: Ensure your Invoice model uses 'paid_amount' or update to 'amount_paid'
                invoice.paid_amount += amount_val 
                invoice.save()

            messages.success(request, f"Successfully recorded UGX {amount_val:,.0f} for {invoice.student.first_name}.")
            return redirect('finance:dashboard')

        except Exception as e:
            messages.error(request, f"Error processing payment: {str(e)}")
            return redirect('finance:record_payment', invoice_id=invoice.id)

    accounts = Account.objects.filter(school=request.school, account_type__iexact='Asset').order_by('name')
    return render(request, 'finance/record_payment.html', {'invoice': invoice, 'accounts': accounts})

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
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    today = timezone.localtime(timezone.now()).date()
    start_date = start_date_str if start_date_str else today
    end_date = end_date_str if end_date_str else today

    # Standardized query
    payments = Payment.objects.filter(
        school=request.school, 
        date_paid__date__range=[start_date, end_date],
        status='Completed'
    ).select_related('invoice', 'invoice__student', 'invoice__student__classroom')

    # FIX: Use amount_paid and payment_method
    total_collected = payments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    summary_by_method = payments.values('payment_method').annotate(total=Sum('amount_paid'))

    return render(request, 'finance/daily_report.html', {
        'payments': payments,
        'total_collected': total_collected,
        'summary_by_method': summary_by_method,
        'start_date': start_date,
        'end_date': end_date,
        'today': today,  # <-- ADD THIS LINE
    })
import openpyxl
from django.http import HttpResponse
from django.utils import timezone
from .models import Payment

def export_collections_excel(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    payments = Payment.objects.filter(
        school=request.school,
        date_paid__date__range=[start_date, end_date]
    ).select_related('invoice__student', 'invoice__student__classroom', 'account')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Collection_Report"

    headers = ['Date', 'Student Name', 'Class', 'Method', 'Account', 'Amount (UGX)', 'Receipt']
    ws.append(headers)

    for p in payments:
        ws.append([
            p.date_paid.strftime('%d/%m/%Y'),
            p.invoice.student.get_full_name(),
            p.invoice.student.classroom.name if p.invoice.student.classroom else "N/A",
            p.payment_method, # FIX: was p.method
            p.account.name if p.account else "N/A",
            p.amount_paid,    # FIX: was p.amount
            p.receipt_number
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Collections_{start_date}.xlsx'
    wb.save(response)
    return response
from django.db.models import Q

from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from .models import Invoice, Payment

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Student, Invoice, Payment

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Invoice, Payment


from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Invoice, Payment
from students.models import Student 

def student_statement(request, student_id):
    # 1. Fetch data securely scoped to the current school
    student = get_object_or_404(Student, id=student_id, school=request.school)
    invoices = Invoice.objects.filter(student=student, school=request.school).order_by('created_at')
    payments = Payment.objects.filter(invoice__student=student, school=request.school).order_by('date_paid')

    ledger = []

    # 2. Add Invoices (Debits) - Safe Date Handling
    for inv in invoices:
        raw_date = inv.created_at or timezone.now()
        # Fix for 'datetime.date' object has no attribute 'date'
        entry_date = raw_date.date() if hasattr(raw_date, 'date') else raw_date
        
        ledger.append({
            'date': entry_date, 
            'description': f"Fees Invoice - {inv.term} {inv.year}",
            'reference': getattr(inv, 'invoice_number', 'INV-SYS'),
            'debit': inv.total_amount,
            'credit': 0,
        })
    
    # 3. Add Payments (Credits) - Using Model field names
    for pay in payments:
        raw_date = pay.date_paid or timezone.now()
        # Fix for 'datetime.date' object has no attribute 'date'
        entry_date = raw_date.date() if hasattr(raw_date, 'date') else raw_date
        
        ledger.append({
            'date': entry_date,
            'description': f"Fee Payment - {pay.payment_method}",
            'reference': pay.transaction_id or pay.receipt_number,
            'debit': 0,
            'credit': pay.amount_paid,
        })

    # 4. Sort and Calculate Balance
    ledger.sort(key=lambda x: x['date'])
    
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
from django.shortcuts import render, redirect
from django.contrib import messages
from students.models import Classroom
from students.forms import ClassroomForm
from .models import FeeStructure
from .forms import FeeStructureForm

def school_settings_hub(request):
    # 1. Fetch data for the lists (Tenancy filter is critical)
    classrooms = Classroom.objects.filter(school=request.school)
    fee_structures = FeeStructure.objects.filter(school=request.school).order_by('-year', 'term')

    # 2. Handle POST requests
    if request.method == "POST":
        form_type = request.POST.get('form_type')

        if form_type == "classroom":
            form = ClassroomForm(request.POST, school=request.school)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.school = request.school
                obj.save()
                messages.success(request, f"Class {obj.name} added successfully!")
                return redirect('finance:settings_hub')

        elif form_type == "fee_structure":
            form = FeeStructureForm(request.POST, school=request.school)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.school = request.school
                obj.save()
                messages.success(request, "Fee structure updated!")
                return redirect('finance:settings_hub')

    # 3. Initialize empty forms for GET request
    context = {
        'class_form': ClassroomForm(school=request.school),
        'fee_form': FeeStructureForm(school=request.school),
        'classrooms': classrooms,
        'fee_structures': fee_structures,
        'fee.school': request.school
    }
    return render(request, 'finance/settings_hub.html', context)



from django.shortcuts import render, get_object_or_404
from .models import Invoice

def print_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, school=request.school)
    # Fetch payments linked to this invoice
    payments = invoice.payments.all()
    
    context = {
        'invoice': invoice,
        'payments': payments,
        'school': request.school, # From your multi-tenant middleware
    }
    return render(request, 'finance/print_invoice.html', context)



from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json

@csrf_exempt
def momo_webhook(request):
    """
    Listens for success/failure signals from the MoMo Provider.
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        tx_ref = data.get('tx_ref')
        status = data.get('status') # e.g., 'successful'

        payment = Payment.objects.filter(transaction_id=tx_ref).first()
        
        if payment and status == 'successful':
            payment.status = 'Completed'
            payment.save() # This triggers Invoice.update_totals() automatically
            return HttpResponse(status=200)
            
    return HttpResponse(status=400)




from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Payment

def check_payment_status(request, payment_id):
    """
    Checks if a Mobile Money payment has been updated 
    to 'Completed' via the Webhook.
    """
    # Ensure we only check payments belonging to the current school/tenant
    payment = get_object_or_404(Payment, id=payment_id, school=request.school)
    
    return JsonResponse({
        'status': payment.status,
        'invoice_id': payment.invoice.id,
        'amount': float(payment.amount_paid),
        'balance': float(payment.invoice.balance)
    })


from students.models import Classroom, Stream
from students.forms import ClassroomForm, StreamForm # Assuming these exist
from .forms import FeeStructureForm
from students.forms import ClassroomForm, StreamForm

def school_settings_hub(request):
    school = request.school
    
    if request.method == "POST":
        form_type = request.POST.get('form_type')

        if form_type == "classroom":
            form = ClassroomForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.school = school
                obj.save()
                messages.success(request, f"Class {obj.name} added!")

        elif form_type == "stream":
            form = StreamForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.school = school
                obj.save()
                messages.success(request, f"Stream {obj.name} added!")

        elif form_type == "fee_structure":
            # Pass school to the form so validation knows which classrooms are valid
            form = FeeStructureForm(request.POST, school=school)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.school = school
                obj.save()
                messages.success(request, "Fee structure saved successfully!")
            else:
                messages.error(request, "Error saving fee structure. Please check details.")

        return redirect('finance:settings_hub')

    # GET request context
    context = {
        'classrooms': Classroom.objects.filter(school=school),
        'streams': Stream.objects.filter(school=school),
        'fee_structures': FeeStructure.objects.filter(school=school).order_by('classroom', 'section'),
        'class_form': ClassroomForm(),
        'stream_form': StreamForm(),
        'fee_form': FeeStructureForm(school=school),
    }
    return render(request, 'finance/settings_hub.html', context)