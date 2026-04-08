import email

import requests
import uuid
from django.conf import settings

import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# Access the hidden data
api_id = os.getenv("SPEEDA_API_ID")
api_password = os.getenv("SPEEDA_API_PASSWORD")
sender_id = os.getenv("SPEEDA_SENDER_ID")

def trigger_momo_payment(phone, amount, invoice_id):
    """
    Sends a request to the MoMo Gateway to prompt the parent for a PIN.
    """
    url = "https://api.payments-gateway.com/v1/stk-push" # Example Gateway URL
    headers = {
        "Authorization": f"Bearer {settings.MOMO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "amount": str(amount),
        "currency": "UGX",
        "phone": phone,
        "metadata": {"invoice_id": invoice_id},
        "callback_url": "https://schooladmin.tech/finance/momo-webhook/", 
        "reference": f"SAO-{uuid.uuid4().hex[:6].upper()}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        return response.json() # Should return a transaction reference
    except Exception as e:
        return {"status": "failed", "message": str(e)}
    




import logging
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

def send_payment_receipt_email(request, payment):
    print("--- STARTING EMAIL FUNCTION ---") 
    try:
        school = request.school 
        student = payment.invoice.student # This is your Student model
        
        recipients = []
        
        # FIX: Changed 'parent_email' to 'guardian_email' to match your model
        if student.guardian_email:
            recipients.append(student.guardian_email)
            logger.info(f"Found Guardian Email: {student.guardian_email}")
        else:
            logger.warning(f"Student {student.get_full_name()} has NO guardian_email.")

        if school.email:
            recipients.append(school.email)
            logger.info(f"Found School Email: {school.email}")

        if not recipients:
            logger.error("!!! EXITING: No recipients found. !!!")
            return False

        subject = f"Receipt {payment.receipt_number} - {student.get_full_name()}"
        
        context = {
            'payment': payment,
            'school': school,
            'student': student, # Added student to context for easier template access
            'protocol': 'https' if request.is_secure() else 'http',
            'domain': get_current_site(request).domain,
            'now': timezone.now(),
        }
        
        html_content = render_to_string('finance/emails/receipt_email.html', context)
        text_content = strip_tags(html_content)
        
        from_email = f"{school.name} <{settings.DEFAULT_FROM_EMAIL}>"
        
        email = EmailMultiAlternatives(subject, text_content, from_email, recipients)
        email.attach_alternative(html_content, "text/html")
        
        email.send(fail_silently=False)
        logger.info(f"Receipt email sent successfully to {', '.join(recipients)}")
        return True

    except Exception as e:
        logger.error(f"Failed to send receipt email: {str(e)}")
        return False
    


import requests
import logging
from django.db import transaction, models
from django.contrib import messages
from django.utils import timezone

# Adjust these imports based on your actual app names
from .models import SMSConfig, SMSTransaction
from students.models import Student

# Initialize Logger
logger = logging.getLogger(__name__)

def send_fee_reminder_sms(request, student):
    """
    Operates a full billing and sending cycle for a single student.
    Costs 100/= per SMS deducted from the school's SMSConfig balance.
    """
    cost_per_sms = 100
    school = request.user.school
    
    # 1. Calculate Balance 
    # Fetches all invoices related to this student and calculates total arrears
    total_billed = student.invoices.aggregate(models.Sum('total_amount'))['total_amount__sum'] or 0
    total_paid = student.invoices.aggregate(models.Sum('paid_amount'))['paid_amount__sum'] or 0
    amount_due = total_billed - total_paid

    if amount_due <= 0:
        return {"status": "F", "remarks": f"No outstanding balance for {student.first_name}."}

    # 2. Check School Wallet (SMSConfig)
    try:
        sms_conf = SMSConfig.objects.get(school=school)
        if sms_conf.balance < cost_per_sms:
            return {"status": "F", "remarks": "Insufficient SMS credits (UGX). Please top up."}
    except SMSConfig.DoesNotExist:
        return {"status": "F", "remarks": "SMS service not configured for your school."}

    # 3. Sanitize Phone Number (SpeedaMobile requires 256...)
    raw_phone = str(student.guardian_phone).strip().replace(" ", "")
    if raw_phone.startswith('0'):
        formatted_phone = '256' + raw_phone[1:]
    elif raw_phone.startswith('+'):
        formatted_phone = raw_phone[1:]
    else:
        formatted_phone = raw_phone

    # 4. Construct Professional Message
    # Note: {amount_due:,} adds commas like 1,000,000 for better readability
    message_text = (
        f"Dear {student.guardian_name}, you are reminded to clear the balance of "
        f"UGX {amount_due:,} for {student.first_name} in {student.classroom}. "
        f"Thank you, {school.name}."
    )

    # 5. Call SpeedaMobile API
    url = "http://apidocs.speedamobile.com/api/SendSMS"
    
    payload = {
        "api_id": api_id, 
        "api_password": api_password,
        "sms_type": "P",
        "encoding": "T",
        "sender_id": sender_id,
        "phonenumber": formatted_phone,
        "textmessage": message_text[:160],
    }

    try:
        # We use a timeout to prevent the system from hanging if the API is slow
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        api_result = response.json()

        # 6. Final Billing Logic: Only deduct if API confirms success ('S')
        if api_result.get("status") == "S":
            with transaction.atomic():
                # select_for_update() prevents multiple requests from double-spending
                wallet = SMSConfig.objects.select_for_update().get(id=sms_conf.id)
                wallet.balance -= cost_per_sms
                wallet.save()
            
            logger.info(f"SMS Sent to {formatted_phone}. 100/= deducted from {school.name}.")
            return {"status": "S", "remarks": f"Reminder sent to {student.guardian_name}."}
        
        return {"status": "F", "remarks": f"Provider Error: {api_result.get('remarks')}"}

    except requests.RequestException as e:
        logger.error(f"Network error for {student.admission_number}: {str(e)}")
        return {"status": "F", "remarks": "Could not connect to SMS Gateway."}

def send_bulk_fee_reminders(request, classroom_id=None):
    """
    Loops through students with arrears and sends reminders.
    Returns (sent_count, fail_count, final_status_message)
    """
    school = request.user.school
    # Get active students with related invoices pre-fetched for performance
    students = Student.objects.filter(school=school, is_active=True).prefetch_related('invoices')
    
    if classroom_id:
        students = students.filter(classroom_id=classroom_id)

    sent_count = 0
    fail_count = 0
    
    for student in students:
        # Check balance again inside the loop for the latest data
        total_billed = student.invoices.aggregate(models.Sum('total_amount'))['total_amount__sum'] or 0
        total_paid = student.invoices.aggregate(models.Sum('paid_amount'))['paid_amount__sum'] or 0
        
        if (total_billed - total_paid) > 0:
            result = send_fee_reminder_sms(request, student)
            if result['status'] == 'S':
                sent_count += 1
            else:
                fail_count += 1
                # If we run out of money, stop the entire loop immediately
                if "Insufficient SMS credits" in result['remarks']:
                    return sent_count, fail_count, "Stopped early: Out of SMS credits."

    return sent_count, fail_count, "Bulk sending complete."



# finance/utils.py

def add_school_credit(school, amount_ugx, user=None):
    """
    Increments school balance and logs the transaction.
    """
    with transaction.atomic():
        config, created = SMSConfig.objects.get_or_create(school=school)
        config.balance += amount_ugx
        config.save()

        SMSTransaction.objects.create(
            school=school,
            amount=amount_ugx,
            transaction_type='TOPUP',
            description=f"Manual Top-up of UGX {amount_ugx:,}",
            performed_by=user
        )
    return config.balance
