from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.utils import timezone


CENT = Decimal('0.01')
ZERO = Decimal('0.00')


class InvalidDiscountCode(ValueError):
    pass


def calculate_checkout_discount(subtotal, code):
    subtotal = Decimal(subtotal).quantize(CENT, rounding=ROUND_HALF_UP)
    normalized_code = (code or '').strip().upper()
    if not normalized_code:
        return normalized_code, ZERO, subtotal
    if subtotal <= ZERO:
        raise InvalidDiscountCode('Discount codes can only be used on a non-empty order.')

    discounts = getattr(settings, 'CHECKOUT_DISCOUNT_CODES', {})
    offer = discounts.get(normalized_code)
    if offer is None:
        raise InvalidDiscountCode('That discount code is not valid.')

    if isinstance(offer, dict):
        percentage = offer.get('percent')
        valid_until = offer.get('valid_until')
        if valid_until:
            if isinstance(valid_until, str):
                try:
                    valid_until = date.fromisoformat(valid_until)
                except ValueError as error:
                    raise ValueError(f'Invalid expiration date configured for discount code {normalized_code}.') from error
            if not isinstance(valid_until, date):
                raise ValueError(f'Invalid expiration date configured for discount code {normalized_code}.')
            if timezone.localdate() > valid_until:
                raise InvalidDiscountCode('That discount code has expired.')
    else:
        percentage = offer

    if percentage is None:
        raise ValueError(f'No percentage configured for discount code {normalized_code}.')
    percentage = Decimal(str(percentage))
    if percentage <= 0 or percentage > 100:
        raise ValueError(f'Invalid percentage configured for discount code {normalized_code}.')

    discount_amount = (subtotal * percentage / Decimal('100')).quantize(
        CENT,
        rounding=ROUND_HALF_UP,
    )
    discount_amount = min(max(discount_amount, ZERO), subtotal)
    return normalized_code, discount_amount, max(subtotal - discount_amount, ZERO)
