from django.conf import settings


def checkout_promotions(request):
    return {
        'checkout_discount_codes': getattr(settings, 'CHECKOUT_DISCOUNT_CODES', {}),
    }
