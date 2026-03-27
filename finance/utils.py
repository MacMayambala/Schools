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