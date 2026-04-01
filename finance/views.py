from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages

from school_management import settings
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
#from .models import Classroom, FeeStructure, Student, Invoice  # Add your specific models here

from django.db import transaction
from django.contrib import messages
from django.shortcuts import render, redirect

@transaction.atomic
def run_bulk_billing(request):
    if request.method == "POST":
        classroom_id = request.POST.get('classroom')
        term = request.POST.get('term')
        year = request.POST.get('year')
        
        # 1. Fetch structures
        structures = FeeStructure.objects.filter(
            classroom_id=classroom_id, 
            term=term, 
            year=year,
            school=request.school
        )

        # DEBUG: Check if we actually found any fees
        print(f"DEBUG: Found {structures.count()} fee structures for Class ID {classroom_id}")

        # Create a normalized map (lowercase keys to avoid "Day" vs "day" issues)
        fee_map = {fs.section.strip().lower(): fs.total_fees for fs in structures}
        print(f"DEBUG: Fee Map created: {fee_map}")

        if not structures.exists():
            messages.error(request, "No Fee Structures found. Create them in the Setup Hub first.")
            return redirect('finance:bulk_billing')

        # 2. Get students
        students = Student.objects.filter(
            classroom_id=classroom_id, 
            school=request.school, 
            is_active=True
        )
        print(f"DEBUG: Found {students.count()} active students in this class.")
        
        count = 0
        skipped = 0

        for student in students:
            # Normalize the student's section for matching
            student_section = student.section.strip().lower() if student.section else "none"
            amount_to_charge = fee_map.get(student_section)

            if amount_to_charge:
                # Use update_or_create if you want to force an update, 
                # or get_or_create to skip if already billed.
                obj, created = Invoice.objects.get_or_create(
                    student=student,
                    term=term,
                    year=year,
                    school=request.school,
                    defaults={'total_amount': amount_to_charge}
                )
                if created:
                    count += 1
            else:
                print(f"DEBUG: Skipping {student.first_name} - No fee found for section '{student_section}'")
                skipped += 1
        
        if count > 0:
            messages.success(request, f"Generated {count} invoices. {skipped} students skipped.")
        else:
            messages.warning(request, f"Zero invoices created. {skipped} students had no matching fee structure.")
            
        return redirect('finance:dashboard')

    classrooms = Classroom.objects.filter(school=request.school)
    return render(request, 'finance/bulk_bill.html', {'classrooms': classrooms})



from django.shortcuts import render, redirect, get_object_or_404
from .models import Invoice, Payment
from .forms import PaymentForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Invoice, Payment
from .forms import PaymentForm
from .utils import send_payment_receipt_email  # Ensure this matches your file structure

# def record_payment(request, invoice_id):
#     # Fetch the invoice ensuring it belongs to the current school/tenant
#     invoice = get_object_or_404(Invoice, id=invoice_id, school=request.school)
    
#     if request.method == 'POST':
#         form = PaymentForm(request.POST)
#         if form.is_valid():
#             # 1. Prepare payment instance without saving to DB yet
#             payment = form.save(commit=False)
            
#             # 2. Assign relationships and Audit data
#             payment.invoice = invoice
#             payment.school = request.school
#             payment.recorded_by = request.user  # Captures the staff member 'serving' the user
            
#             # 3. Save to DB (triggers receipt_number generation & invoice total updates)
#             payment.save()
            
#             # 4. Trigger the branded email receipt
#             success = send_payment_receipt_email(request, payment)
            
#             # 5. Provide feedback to the staff member
#             if success:
#                 messages.success(request, f"Payment of {payment.amount_paid} recorded and receipt sent to parent.")
#             else:
#                 messages.warning(request, f"Payment of {payment.amount_paid} recorded, but receipt email failed to send.")
            
#             return redirect('finance:receipt_detail', payment_id=payment.id)
            
#     else:
#         # Default the payment amount to the remaining invoice balance
#         form = PaymentForm(initial={'amount_paid': invoice.balance})
        
#     return render(request, 'finance/record_payment.html', {
#         'form': form, 
#         'invoice': invoice
#     })

def receipt_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, school=request.school)
    return render(request, 'finance/receipt.html', {'payment': payment})



import logging
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings

# Get an instance of a logger
logger = logging.getLogger(__name__)

def send_payment_receipt_email(request, payment):
    try:
        current_site = get_current_site(request)
        school = request.school 
        
        # 1. VALIDATE RECIPIENTS (The #1 reason emails fail)
        recipients = []
        
        # Check parent email
        if payment.invoice.student.parent_email:
            recipients.append(payment.invoice.student.parent_email)
        
        # Check school email
        if school.email:
            recipients.append(school.email)

        if not recipients:
            logger.warning(f"No recipients found for Payment {payment.receipt_number}. Email skipped.")
            return False

        # 2. PREPARE CONTENT
        subject = f"Receipt {payment.receipt_number} from {school.name}"
        context = {
            'payment': payment,
            'school': school,
            'protocol': 'https' if request.is_secure() else 'http',
            'domain': current_site.domain,
            'now': timezone.now(),
        }
        
        html_content = render_to_string('finance/emails/receipt_email.html', context)
        text_content = strip_tags(html_content)
        
        # 3. CONSTRUCT EMAIL
        # Format the 'From' address properly: "School Name <system@mail.com>"
        from_email = f"{school.name} <{settings.DEFAULT_FROM_EMAIL}>"
        
        email = EmailMultiAlternatives(
            subject, 
            text_content, 
            from_email, 
            recipients
        )
        email.attach_alternative(html_content, "text/html")
        
        # 4. SEND
        email.send(fail_silently=False)
        logger.info(f"Email sent successfully for {payment.receipt_number} to {recipients}")
        return True

    except Exception as e:
        # This will show up in your terminal/logs
        logger.error(f"Failed to send receipt email for {payment.receipt_number}: {str(e)}")
        return False

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


from decimal import Decimal
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Invoice, Payment, Account
from .utils import send_payment_receipt_email  # Import your email utility

def record_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, school=request.school)
    
    if request.method == "POST":
        try:
            with transaction.atomic():
                # 1. Map incoming POST data
                amount_val = Decimal(request.POST.get('amount'))
                target_account = get_object_or_404(Account, id=request.POST.get('account'), school=request.school)

                # 2. Create the payment record
                payment = Payment.objects.create(
                    school=request.school,
                    invoice=invoice,
                    amount_paid=amount_val,
                    payment_method=request.POST.get('method'),
                    transaction_id=request.POST.get('reference'),
                    depositor=request.POST.get('depositor'),
                    phone_number=request.POST.get('phone_number'), # Added phone
                    recorded_by=request.user,
                    status='Completed'
                )

                # 3. Financial Updates
                target_account.balance += amount_val
                target_account.save()

                # 4. Update the Invoice Balance
                # Ensure your model field name is correct (paid_amount vs amount_paid)
                invoice.paid_amount += amount_val 
                invoice.save()

            # 5. TRIGGER EMAIL (Outside the atomic block is safer for performance)
            email_success = send_payment_receipt_email(request, payment)

            if email_success:
                messages.success(request, f"Successfully recorded UGX {amount_val:,.0f}. Receipt sent to parent.")
            else:
                messages.success(request, f"Payment recorded, but receipt email skipped (check parent email address).")
            
            return redirect('finance:dashboard')

        except Exception as e:
            messages.error(request, f"Error processing payment: {str(e)}")
            return redirect('finance:record_payment', invoice_id=invoice.id)

    # Filter for Asset accounts (Cash, Bank, Mobile Money)
    accounts = Account.objects.filter(school=request.school, account_type__iexact='Asset').order_by('name')
    
    context = {
        'invoice': invoice, 
        'accounts': accounts,
        'remaining_balance': invoice.balance # Useful for the frontend template
    }
    return render(request, 'finance/record_payment.html', context)



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
from students.models import Classroom, Stream
from students.forms import ClassroomForm, StreamForm
from .models import FeeStructure
from .forms import FeeStructureForm

def school_settings_hub(request):
    school = request.school
    
    # 1. Fetch data for the dashboard
    classrooms = Classroom.objects.filter(school=school).order_by('level')
    streams = Stream.objects.filter(school=school)
    fee_structures = FeeStructure.objects.filter(school=school).select_related('classroom').order_by('-year', 'term')

    # 2. Initialize forms (Default to empty)
    class_form = ClassroomForm(school=school)
    stream_form = StreamForm(school=school)
    fee_form = FeeStructureForm(school=school)

    # 3. Handle POST requests
    if request.method == "POST":
        form_type = request.POST.get('form_type')

        if form_type == "classroom":
            class_form = ClassroomForm(request.POST, school=school)
            if class_form.is_valid():
                obj = class_form.save(commit=False)
                obj.school = school
                obj.save()
                messages.success(request, f"Class {obj.name} added successfully!")
                return redirect('finance:settings_hub')

        elif form_type == "stream":
            stream_form = StreamForm(request.POST, school=school)
            if stream_form.is_valid():
                obj = stream_form.save(commit=False)
                obj.school = school
                obj.save()
                messages.success(request, f"Stream {obj.name} added!")
                return redirect('finance:settings_hub')

        elif form_type == "fee_structure":
            fee_form = FeeStructureForm(request.POST, school=school)
            if fee_form.is_valid():
                obj = fee_form.save(commit=False)
                obj.school = school
                obj.save()
                messages.success(request, "Fee structure updated!")
                return redirect('finance:settings_hub')
        
        # If any form is invalid, the code continues to the render() 
        # carrying the 'form' instances (with their error messages).

    context = {
        'class_form': class_form,
        'stream_form': stream_form,
        'fee_form': fee_form,
        'classrooms': classrooms,
        'streams': streams,
        'fee_structures': fee_structures,
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




from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .utils import send_bulk_fee_reminders

@login_required
def bulk_sms_reminder_view(request):
    """
    View to trigger bulk SMS reminders for all students with arrears.
    """
    # Optional: Get classroom_id from GET parameters if filtering by class
    classroom_id = request.GET.get('classroom_id')
    
    # Call the utility function
    sent, failed, status_msg = send_bulk_fee_reminders(request, classroom_id)
    
    if sent > 0:
        messages.success(request, f"Successfully sent {sent} fee reminders.")
    
    if failed > 0:
        # If some failed (usually due to balance or invalid phone numbers)
        messages.warning(request, f"Failed to send {failed} messages. Status: {status_msg}")
    
    if sent == 0 and failed == 0:
        messages.info(request, "No students with outstanding balances were found.")

    # Redirect back to the finance dashboard or student list
    return redirect(request.META.get('HTTP_REFERER', 'finance:dashboard'))




