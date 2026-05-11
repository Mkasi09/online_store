"""
Paystack Payment Gateway Integration for iPhone Store
"""

import json
import requests
from django.conf import settings
from django.urls import reverse


class PaystackConfig:
    """Paystack configuration settings"""
    
    @classmethod
    def get_secret_key(cls):
        """Get Paystack secret key from settings"""
        return getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    
    @classmethod
    def get_public_key(cls):
        """Get Paystack public key from settings"""
        return getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
    
    @classmethod
    def get_payment_url(cls):
        """Get Paystack payment initialization URL"""
        return getattr(settings, 'PAYSTACK_PAYMENT_URL', 'https://api.paystack.co/transaction/initialize')
    
    @classmethod
    def is_test_mode(cls):
        """Check if Paystack is in test mode"""
        return getattr(settings, 'PAYSTACK_MODE', 'test') == 'test'


class PaystackPayment:
    def __init__(self, order, request):
        self.order = order
        self.request = request
        self.config = PaystackConfig()

    def initialize_transaction(self):
        """
        Initialize a Paystack transaction
        
        Returns:
            dict: Paystack response containing authorization URL
        """
        request = self.request
        domain = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        base_url = f"{scheme}://{domain}"
        
        # Prepare callback URLs
        callback_url = f"{base_url}/payment/paystack/callback/"
        success_url = f"{base_url}/payment/success/"
        cancel_url = f"{base_url}/payment/cancel/"
        
        # Prepare payload for Paystack API
        payload = {
            'email': self.order.email,
            'amount': int(self.order.total_amount * 100),  # Convert to kobo/cents
            'currency': 'ZAR',  # South African Rand
            'reference': f"order_{self.order.id}_{self.order.id}",  # Unique reference
            'callback_url': callback_url,
            'metadata': {
                'order_id': self.order.id,
                'custom_fields': [
                    {
                        'display_name': 'Order ID',
                        'variable_name': 'order_id',
                        'value': str(self.order.id)
                    },
                    {
                        'display_name': 'Customer Email',
                        'variable_name': 'customer_email',
                        'value': self.order.email
                    }
                ]
            }
        }
        
        headers = {
            'Authorization': f'Bearer {self.config.get_secret_key()}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                self.config.get_payment_url(),
                data=json.dumps(payload),
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                'status': False,
                'message': f'Payment initialization failed: {str(e)}'
            }

    def verify_transaction(self, reference):
        """
        Verify a Paystack transaction using the reference
        
        Args:
            reference: The transaction reference from Paystack
            
        Returns:
            dict: Verification response
        """
        verify_url = f"https://api.paystack.co/transaction/verify/{reference}"
        
        headers = {
            'Authorization': f'Bearer {self.config.get_secret_key()}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(verify_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                'status': False,
                'message': f'Transaction verification failed: {str(e)}'
            }

    def get_payment_form(self):
        """
        Generate HTML form for Paystack payment
        
        Returns:
            str: HTML form with Paystack script
        """
        # Initialize transaction first
        init_response = self.initialize_transaction()
        
        if not init_response.get('status'):
            return f"""
            <div class="alert alert-danger">
                Payment initialization failed: {init_response.get('message', 'Unknown error')}
            </div>
            """
        
        data = init_response.get('data', {})
        authorization_url = data.get('authorization_url')
        access_code = data.get('access_code')
        reference = data.get('reference')
        
        if not authorization_url:
            return """
            <div class="alert alert-danger">
                No authorization URL received from Paystack
            </div>
            """
        
        return f"""
        <div id="paystack-payment-container">
            <script src="https://js.paystack.co/v1/inline.js"></script>
            <script>
                function payWithPaystack() {{
                    var handler = PaystackPop.setup({{
                        key: '{self.config.get_public_key()}',
                        email: '{self.order.email}',
                        amount: {int(self.order.total_amount * 100)},
                        currency: 'ZAR',
                        reference: '{reference}',
                        callback: function(response) {{
                            window.location.href = '/payment/paystack/callback/?reference=' + response.reference;
                        }},
                        onClose: function() {{
                            window.location.href = '/payment/cancel/';
                        }}
                    }});
                    handler.openIframe();
                }}
                
                // Auto-open payment modal
                document.addEventListener('DOMContentLoaded', function() {{
                    setTimeout(payWithPaystack, 1000);
                }});
            </script>
            
            <div class="text-center">
                <button type="button" class="btn btn-success" onclick="payWithPaystack()">
                    Pay with Paystack
                </button>
                <p class="mt-2">
                    <small>Secure payment powered by Paystack</small>
                </p>
            </div>
        </div>
        """


def process_paystack_callback(reference, order):
    """
    Process Paystack payment callback
    
    Args:
        reference: Transaction reference from Paystack
        order: Order object
        
    Returns:
        dict: Processing result
    """
    payment = PaystackPayment(order, None)
    verification = payment.verify_transaction(reference)
    
    if verification.get('status') and verification.get('data', {}).get('status') == 'success':
        return {
            'success': True,
            'message': 'Payment successful',
            'transaction_data': verification.get('data', {})
        }
    else:
        return {
            'success': False,
            'message': verification.get('message', 'Payment verification failed'),
            'transaction_data': verification.get('data', {})
        }
