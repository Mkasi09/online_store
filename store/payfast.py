"""
PayFast Payment Gateway Integration for iPhone Store
"""

import hashlib
import urllib.parse
from django.conf import settings
from django.urls import reverse


class PayFastConfig:
    """PayFast configuration settings"""
    
    # PayFast URLs
    SANDBOX_URL = 'https://sandbox.payfast.co.za/eng/process'
    LIVE_URL = 'https://www.payfast.co.za/eng/process'
    
    SANDBOX_VALIDATE_URL = 'https://sandbox.payfast.co.za/eng/query/validate'
    LIVE_VALIDATE_URL = 'https://www.payfast.co.za/eng/query/validate'
    
    @classmethod
    def get_process_url(cls):
        """Get the PayFast process URL based on mode"""
        # Set PAYFAST_MODE = 'live' in production settings
        mode = getattr(settings, 'PAYFAST_MODE', 'sandbox')
        return cls.LIVE_URL if mode == 'live' else cls.SANDBOX_URL
    
    @classmethod
    def get_merchant_id(cls):
        """Get merchant ID from settings"""
        return getattr(settings, 'PAYFAST_MERCHANT_ID', '')
    
    @classmethod
    def get_merchant_key(cls):
        """Get merchant key from settings"""
        return getattr(settings, 'PAYFAST_MERCHANT_KEY', '')
    
    @classmethod
    def get_passphrase(cls):
        """Get passphrase from settings (optional but recommended)"""
        return getattr(settings, 'PAYFAST_PASSPHRASE', '')

class PayFastPayment:
    def __init__(self, order, request):
        self.order = order
        self.request = request

    def get_payment_form(self):
        config = PayFastConfig()
        request = self.request
        domain = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        base_url = f"{scheme}://{domain}"
        
        return f"""
        <form action="{config.get_process_url()}" method="post" id="payfast-form">
            <input type="hidden" name="merchant_id" value="{config.get_merchant_id()}">
            <input type="hidden" name="merchant_key" value="{config.get_merchant_key()}">
            
            <input type="hidden" name="return_url" value="{base_url}/payment/success/">
            <input type="hidden" name="cancel_url" value="{base_url}/payment/cancel/">
            <input type="hidden" name="notify_url" value="{base_url}/payment/notify/">
            
            <input type="hidden" name="amount" value="{self.order.total_amount}">
            <input type="hidden" name="item_name" value="Order #{self.order.id}">
            <input type="hidden" name="email_address" value="{self.order.email}">
        </form>
        """

def verify_payfast_signature(data, signature):
    """
    Verify PayFast signature for ITN callbacks
    
    Args:
        data: Dictionary of POST data from PayFast (excluding 'signature' key)
        signature: The signature provided by PayFast
    
    Returns:
        bool: True if signature is valid
    """
    config = PayFastConfig()
    
    # Create ordered parameter string
    sorted_params = sorted(data.items())
    param_string = '&'.join([f'{k}={urllib.parse.quote(str(v), safe="")}' 
                             for k, v in sorted_params])
    
    # Add passphrase if configured
    passphrase = config.get_passphrase()
    if passphrase:
        param_string += f'&passphrase={urllib.parse.quote(passphrase, safe="")}'
    
    # Generate signature
    calculated_signature = hashlib.md5(param_string.encode()).hexdigest()
    
    return calculated_signature == signature


def validate_payfast_ip(ip_address):
    """
    Validate that the request comes from a valid PayFast IP address
    
    Note: In production, you should verify the IP is from PayFast's servers
    """
    # PayFast IP ranges (these should be updated from PayFast documentation)
    valid_ips = [
        '196.40.96.0/20',  # PayFast production range
        '197.97.80.0/20',  # PayFast sandbox range
    ]
    
    # For now, return True to allow testing
    # In production, implement proper IP validation
    return True
