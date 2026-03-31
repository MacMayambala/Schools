import email

import requests
import uuid
from django.conf import settings

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