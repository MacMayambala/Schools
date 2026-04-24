# finance/context_processors.py
from decimal import Decimal
from django.db.models import Sum
from .models import Invoice, SMSConfig


def school_financials(request):
    """
    Context processor that adds school-wide financial data and SMS balance
    to every template (including the dashboard).
    """
    if not (request.user.is_authenticated and hasattr(request.user, 'school') and request.user.school):
        return {}

    school = request.user.school

    # === Financial Totals ===
    invoices = Invoice.objects.filter(school=school)

    total_expected = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    total_collected = invoices.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0.00')

    # === SMS Configuration ===
    # Use get_or_create so every school always has a config
    sms_conf, _ = SMSConfig.objects.get_or_create(
        school=school,
        defaults={
            'balance': Decimal('0.00'),
            'cost_per_sms': Decimal('100.00')
        }
    )

    return {
        'total_expected': total_expected,
        'total_collected': total_collected,
        'balance': total_expected - total_collected,

        # SMS related
        'sms_credit': sms_conf.remaining_messages,      # e.g. 45 messages
        'raw_sms_balance': sms_conf.balance,            # raw UGX amount
        'sms_cost_per_message': sms_conf.cost_per_sms,
    }