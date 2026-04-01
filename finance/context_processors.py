# finance/context_processors.py
from .models import Invoice, SMSConfig
from django.db.models import Sum

def school_financials(request):
    if request.user.is_authenticated and hasattr(request.user, 'school'):
        # Financial Calculations
        total_expected = Invoice.objects.filter(school=request.user.school).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_collected = Invoice.objects.filter(school=request.user.school).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
        
        # SMS Logic
        sms_conf, created = SMSConfig.objects.get_or_create(school=request.user.school)
        
        return {
            'total_expected': total_expected,
            'total_collected': total_collected,
            'balance': total_expected - total_collected,
            'sms_credit': sms_conf.remaining_messages, # Returns the count (e.g., 50 messages)
            'raw_sms_balance': sms_conf.balance # In case you want to show UGX balance
        }
    return {}