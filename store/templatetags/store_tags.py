from django import template

from django.contrib.sessions.models import Session

from ..models import Cart, CartItem



register = template.Library()



@register.simple_tag

def get_cart_count(user):

    """Get the number of items in the user's cart"""

    if user.is_authenticated:

        # Try to get cart by session key

        session_key = None

        if hasattr(user, 'session') and user.session.session_key:

            session_key = user.session.session_key

        

        if session_key:

            try:

                cart = Cart.objects.get(session_key=session_key)

                return cart.get_total_items()

            except Cart.DoesNotExist:

                pass

    

    return 0



@register.simple_tag

def get_cart_total(user):

    """Get the total price of items in the user's cart"""

    if user.is_authenticated:

        # Try to get cart by session key

        session_key = None

        if hasattr(user, 'session') and user.session.session_key:

            session_key = user.session.session_key

        

        if session_key:

            try:

                cart = Cart.objects.get(session_key=session_key)

                return cart.get_total_price()

            except Cart.DoesNotExist:

                pass

    

    return 0

