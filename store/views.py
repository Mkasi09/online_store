from django.shortcuts import render, get_object_or_404, redirect







from django.db.models import Q







from django.views.generic import ListView, DetailView, View







from django.views import View







from django.contrib import messages







from django.http import JsonResponse







from django.utils.decorators import method_decorator







from django.views.decorators.csrf import csrf_exempt







from django.contrib.auth import login, authenticate, logout







from django.contrib.auth.decorators import login_required







from django.contrib.auth.mixins import LoginRequiredMixin







from django.contrib.auth.models import User







from django.contrib.auth.forms import AuthenticationForm







from .models import iPhoneProduct, iPhoneModel, Color, Cart, CartItem, Order, OrderItem







from .forms import CustomUserCreationForm







from .payfast import PayFastPayment, verify_payfast_signature







import json
import logging







import uuid







from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import send_mail


logger = logging.getLogger(__name__)















class ProductListView(ListView):







    model = iPhoneProduct







    template_name = 'store/product_list.html'







    context_object_name = 'products'







    paginate_by = 12







    







    def get_queryset(self):







        queryset = iPhoneProduct.objects.filter(is_active=True)







        







        # Search functionality







        search_query = self.request.GET.get('search', '')







        if search_query:







            queryset = queryset.filter(







                Q(iphone_model__name__icontains=search_query) |







                Q(color__name__icontains=search_query) |







                Q(storage__icontains=search_query)







            )







        







        # Filter by model







        model_filter = self.request.GET.get('model', '')







        if model_filter:







            queryset = queryset.filter(iphone_model__name=model_filter)







        







        # Filter by color







        color_filter = self.request.GET.get('color', '')







        if color_filter:







            queryset = queryset.filter(color__name=color_filter)







        







        # Filter by storage







        storage_filter = self.request.GET.get('storage', '')







        if storage_filter:







            queryset = queryset.filter(storage=storage_filter)







        







        # Filter by condition







        condition_filter = self.request.GET.get('condition', '')







        if condition_filter:







            queryset = queryset.filter(condition=condition_filter)







        







        # Sort by







        sort_by = self.request.GET.get('sort', 'newest')







        if sort_by == 'price_low':







            queryset = queryset.order_by('price')







        elif sort_by == 'price_high':







            queryset = queryset.order_by('-price')







        elif sort_by == 'name':







            queryset = queryset.order_by('iphone_model__name')







        else:  # newest







            queryset = queryset.order_by('-created_at')







        







        return queryset







    







    def get_context_data(self, **kwargs):







        context = super().get_context_data(**kwargs)







        







        # Add filter options







        context['models'] = iPhoneModel.objects.all()







        context['colors'] = Color.objects.all()







        context['storage_options'] = iPhoneProduct.STORAGE_CHOICES







        context['condition_options'] = iPhoneProduct.CONDITION_CHOICES







        







        # Add current filter values







        context['current_search'] = self.request.GET.get('search', '')







        context['current_model'] = self.request.GET.get('model', '')







        context['current_color'] = self.request.GET.get('color', '')







        context['current_storage'] = self.request.GET.get('storage', '')







        context['current_condition'] = self.request.GET.get('condition', '')







        context['current_sort'] = self.request.GET.get('sort', 'newest')







        







        return context















class ProductDetailView(DetailView):







    model = iPhoneProduct







    template_name = 'store/product_detail.html'







    context_object_name = 'product'







    







    def get_queryset(self):







        return iPhoneProduct.objects.filter(is_active=True)







    







    def get_context_data(self, **kwargs):







        context = super().get_context_data(**kwargs)







        product = self.get_object()







        







        # Get related products (same model, different colors or storage)







        related_products = iPhoneProduct.objects.filter(







            iphone_model=product.iphone_model,







            is_active=True







        ).exclude(pk=product.pk)[:4]







        







        # Get storage variants for the same model and color



        storage_variants = iPhoneProduct.objects.filter(



            iphone_model=product.iphone_model,



            color=product.color,



            is_active=True



        ).order_by('storage')







        # Get color variants for the same model



        color_variants = iPhoneProduct.objects.filter(



            iphone_model=product.iphone_model,



            storage=product.storage,



            is_active=True



        ).select_related('color').order_by('color__name')







        context['related_products'] = related_products



        context['storage_variants'] = storage_variants



        context['color_variants'] = color_variants







        return context















class CartView(View):







    def get(self, request):







        cart = self.get_or_create_cart()







        cart_items = cart.cartitem_set.all()







        







        # Calculate estimated delivery date (5 business days excluding weekends)
        from datetime import datetime, timedelta
        start_date = datetime.now().date()
        business_days = 5
        days_added = 0
        current_date = start_date
        
        while days_added < business_days:
            current_date += timedelta(days=1)
            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() < 5:
                days_added += 1
        
        estimated_delivery = current_date

        

        context = {

            'cart': cart,

            'cart_items': cart_items,

            'estimated_delivery_date': estimated_delivery,

        }

        return render(request, 'store/cart.html', context)







    







    def get_or_create_cart(self):







        session_key = self.request.session.session_key







        if not session_key:







            self.request.session.create()







            session_key = self.request.session.session_key







        







        cart, created = Cart.objects.get_or_create(session_key=session_key)







        return cart















class AddToCartView(View):







    def post(self, request, product_id):







        product = get_object_or_404(iPhoneProduct, id=product_id, is_active=True)







        quantity = int(request.POST.get('quantity', 1))







        







        if product.stock_quantity < quantity:







            messages.error(request, f'Sorry, only {product.stock_quantity} items available in stock.')







            return redirect('store:product_detail', pk=product_id)







        







        # Get or create cart for this session



        session_key = request.session.session_key



        if not session_key:



            request.session.create()



            session_key = request.session.session_key



        



        cart, created = Cart.objects.get_or_create(session_key=session_key)







        







        cart_item, created = CartItem.objects.get_or_create(







            cart=cart,







            product=product,







            defaults={'quantity': quantity}







        )







        







        if not created:







            cart_item.quantity += quantity







            cart_item.save()







        







        messages.success(request, f'{product.iphone_model.name} added to cart!')







        return redirect('store:cart')















class UpdateCartView(View):







    def post(self, request, item_id):







        cart_item = get_object_or_404(CartItem, id=item_id)







        quantity = int(request.POST.get('quantity', 1))







        







        if quantity <= 0:







            cart_item.delete()







            messages.success(request, 'Item removed from cart.')







        elif quantity <= cart_item.product.stock_quantity:







            cart_item.quantity = quantity







            cart_item.save()







            messages.success(request, 'Cart updated successfully.')







        else:







            messages.error(request, f'Sorry, only {cart_item.product.stock_quantity} items available.')







        







        return redirect('store:cart')















class RemoveFromCartView(View):







    def post(self, request, item_id):







        cart_item = get_object_or_404(CartItem, id=item_id)







        cart_item.delete()







        messages.success(request, 'Item removed from cart.')







        return redirect('store:cart')















@method_decorator(csrf_exempt, name='dispatch')







class CartSummaryView(View):







    def get(self, request):



        # Get or create cart for this session



        session_key = request.session.session_key



        if not session_key:



            request.session.create()



            session_key = request.session.session_key



        



        cart, created = Cart.objects.get_or_create(session_key=session_key)



        



        data = {



            'total_items': cart.get_total_items(),



            'total_price': float(cart.get_total_price()),



        }







        







        return JsonResponse(data)















def home(request):
    # Get featured products with one product from each model.
    featured_products = []
    featured_models = iPhoneModel.objects.filter(
        iphoneproduct__is_active=True,
    ).distinct().order_by('-release_year', 'name')[:8]
    for model in featured_models:
        product = iPhoneProduct.objects.filter(
            iphone_model=model,
            is_active=True,
            condition='new',
        ).order_by('price').first()
        if product is None:
            product = iPhoneProduct.objects.filter(
                iphone_model=model,
                is_active=True,
            ).order_by('price').first()
        if product is not None:
            featured_products.append(product)
    
    # Get new phones
    new_phones = iPhoneProduct.objects.filter(is_active=True, condition='new').order_by('-created_at')[:4]
    
    # Get pre-owned phones from requested model families.
    pre_owned_model_names = ('iPhone 11', 'iPhone XR', 'iPhone 12 Pro', 'iPhone 13')
    pre_owned_phones = []
    for model_name in pre_owned_model_names:
        product = iPhoneProduct.objects.filter(
            iphone_model__name=model_name,
            is_active=True,
            condition__in=['used', 'refurbished'],
        ).order_by('price').first()
        if product is not None:
            pre_owned_phones.append(product)

    latest_models = iPhoneModel.objects.all().order_by('-release_year')[:6]

    context = {
        'featured_products': featured_products,
        'new_phones': new_phones,
        'pre_owned_phones': pre_owned_phones,
        'latest_models': latest_models,
    }

    return render(request, 'store/home.html', context)















# Authentication Views







def register(request):







    if request.method == 'POST':







        form = CustomUserCreationForm(request.POST)







        if form.is_valid():







            user = form.save()







            username = form.cleaned_data.get('username')







            







            # Check if this is an AJAX request (from modal)







            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':







                return JsonResponse({'success': True, 'message': f'Account created for {username}!'})







            







            messages.success(request, f'Account created for {username}! You can now log in.')







            return redirect('store:login')







        else:







            # Check if this is an AJAX request (from modal)







            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':







                errors = dict(form.errors.items())







                return JsonResponse({'success': False, 'error': 'Registration failed', 'errors': errors})







    else:







        form = CustomUserCreationForm()







    







    # For regular page load, render the template







    return render(request, 'store/register.html', {'form': form})















def custom_login(request):







    if request.method == 'POST':







        form = AuthenticationForm(request, data=request.POST)







        if form.is_valid():







            username = form.cleaned_data.get('username')







            password = form.cleaned_data.get('password')







            user = authenticate(username=username, password=password)







            if user is not None:







                login(request, user)







                







                # Check if this is an AJAX request (from modal)







                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':







                    return JsonResponse({'success': True, 'message': f'Welcome back, {username}!'})







                







                messages.success(request, f'Welcome back, {username}!')







                return redirect('store:home')







            else:







                error_message = 'Invalid username or password.'







                







                # Check if this is an AJAX request (from modal)







                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':







                    return JsonResponse({'success': False, 'error': error_message})







                







                messages.error(request, error_message)







        else:







            error_message = 'Invalid username or password.'







            







            # Check if this is an AJAX request (from modal)







            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':







                errors = dict(form.errors.items())







                return JsonResponse({'success': False, 'error': error_message, 'errors': errors})







            







            messages.error(request, error_message)







    else:







        form = AuthenticationForm()







    







    # For regular page load, render the template







    return render(request, 'store/login.html', {'form': form})















def custom_logout(request):



    logout(request)



    messages.success(request, 'You have been logged out successfully.')



    return redirect('store:home')















@login_required







def profile(request):







    return render(request, 'store/profile.html')















@login_required







def update_profile(request):







    if request.method == 'POST':







        user = request.user







        user.first_name = request.POST.get('first_name', user.first_name)







        user.last_name = request.POST.get('last_name', user.last_name)







        user.email = request.POST.get('email', user.email)







        user.save()







        messages.success(request, 'Profile updated successfully!')







        return redirect('store:profile')







    







    return redirect('store:profile')















def send_manual_payment_email(order, request):
    """Send bank details and proof-of-payment instructions for a new order."""
    try:
        bank_details = [
            f"Bank: {settings.ORDER_PAYMENT_BANK_NAME}",
            f"Account name: {settings.ORDER_PAYMENT_ACCOUNT_NAME}",
            f"Account number: {settings.ORDER_PAYMENT_ACCOUNT_NUMBER}",
            f"Branch code: {settings.ORDER_PAYMENT_BRANCH_CODE}",
            f"Account type: {settings.ORDER_PAYMENT_ACCOUNT_TYPE}",
            f"Reference: {order.order_number}",
        ]
        proof_email = settings.ORDER_PAYMENT_PROOF_EMAIL
        whatsapp = settings.ORDER_PAYMENT_WHATSAPP
        order_url = request.build_absolute_uri(order.get_absolute_url())

        customer_name = order.user.get_full_name() or order.user.username
        message = (
            f"Hi {customer_name},\n\n"
            f"Thank you for your order #{order.order_number}.\n\n"
            f"Amount due: R{order.total_amount}\n\n"
            "Please pay using the banking details below:\n"
            f"{chr(10).join(bank_details)}\n\n"
            "After making payment, please send proof of payment by email or WhatsApp:\n"
            f"Email: {proof_email}\n"
            f"WhatsApp: {whatsapp}\n\n"
            "Your order status will be updated to Processing once proof of payment has been received and confirmed.\n\n"
            f"View your order: {order_url}\n\n"
            "Thank you,\n"
            "iPhone Store"
        )

        sent_count = send_mail(
            subject=f"Order #{order.order_number} payment instructions",
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=[order.email],
            fail_silently=False,
        )
        return sent_count > 0
    except BaseException:
        logger.exception("Failed to send payment email for order %s", order.order_number)
        return False


@login_required



def checkout(request):



    if request.method == 'POST':



        try:



            # Ensure session exists



            if not request.session.session_key:



                request.session.create()



            



            # Get cart directly



            cart = Cart.objects.get_or_create(session_key=request.session.session_key)[0]



            cart_items = cart.cartitem_set.all()



            



            if not cart_items:



                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':



                    return JsonResponse({'success': False, 'error': 'Your cart is empty'})



                messages.error(request, 'Your cart is empty')



                return redirect('store:cart')



            



            # Get new address fields



            shipping_street = request.POST.get('shipping_street', '').strip()



            shipping_town = request.POST.get('shipping_town', '').strip()



            shipping_city = request.POST.get('shipping_city', '').strip()



            shipping_province = request.POST.get('shipping_province', '').strip()



            shipping_postal = request.POST.get('shipping_postal', '').strip()



            



            billing_street = request.POST.get('billing_street', '').strip()



            billing_town = request.POST.get('billing_town', '').strip()



            billing_city = request.POST.get('billing_city', '').strip()



            billing_province = request.POST.get('billing_province', '').strip()



            billing_postal = request.POST.get('billing_postal', '').strip()



            



            email = request.POST.get('email', '').strip()



            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'



            



            # Validate required fields



            if not all([shipping_street, shipping_town, shipping_city, shipping_province, shipping_postal]):



                if is_ajax:



                    return JsonResponse({'success': False, 'error': 'Complete shipping address is required'})



                messages.error(request, 'Complete shipping address is required')



                return redirect('store:cart')



            



            if not all([billing_street, billing_town, billing_city, billing_province, billing_postal]):



                if is_ajax:



                    return JsonResponse({'success': False, 'error': 'Complete billing address is required'})



                messages.error(request, 'Complete billing address is required')



                return redirect('store:cart')



            



            if not email:



                if is_ajax:



                    return JsonResponse({'success': False, 'error': 'Email is required'})



                messages.error(request, 'Email is required')



                return redirect('store:cart')



            



            # Build full address strings for display



            shipping_address = f"{shipping_street}, {shipping_town}, {shipping_city}, {shipping_province}, {shipping_postal}"



            billing_address = f"{billing_street}, {billing_town}, {billing_city}, {billing_province}, {billing_postal}"



            

            for cart_item in cart_items:
                if cart_item.quantity > cart_item.product.stock_quantity:
                    error = f'Sorry, only {cart_item.product.stock_quantity} {cart_item.product.iphone_model.name} available.'
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': error})
                    messages.error(request, error)
                    return redirect('store:cart')



            total_amount = cart.get_total_price()
            phone = request.POST.get('phone', '').strip()
            notes = request.POST.get('notes', '').strip()

            order = Order.objects.create(
                user=request.user,
                session_key=request.session.session_key,
                status='pending_payment',
                payment_status='pending',
                total_amount=total_amount,
                shipping_street=shipping_street,
                shipping_town=shipping_town,
                shipping_city=shipping_city,
                shipping_province=shipping_province,
                shipping_postal=shipping_postal,
                billing_street=billing_street,
                billing_town=billing_town,
                billing_city=billing_city,
                billing_province=billing_province,
                billing_postal=billing_postal,
                shipping_address=shipping_address,
                billing_address=billing_address,
                email=email,
                phone=phone,
                notes=notes,
            )

            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                )
                cart_item.product.stock_quantity -= cart_item.quantity
                cart_item.product.save()

            cart.cartitem_set.all().delete()
            email_sent = send_manual_payment_email(order, request)

            if email_sent:
                messages.success(
                    request,
                    'Order placed. Banking details have been emailed to you. '
                    'Send proof of payment by email or WhatsApp so your order can be processed.'
                )
            else:
                messages.warning(
                    request,
                    'Order placed. Email could not be sent, but your banking details are shown on this order page.'
                )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'order_number': order.order_number,
                    'email_sent': email_sent,
                    'payment_required': False,
                    'redirect_url': order.get_absolute_url(),
                })

            return redirect('store:order_detail', order_id=order.id)



            



        except Exception as e:



            import traceback



            error_msg = str(e)



            tb = traceback.format_exc()



            print(f"CHECKOUT ERROR: {error_msg}")



            print(tb)



            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':



                return JsonResponse({'success': False, 'error': f'Error: {error_msg}'})



            # Show error page with details instead of redirecting



            return render(request, 'store/checkout_error.html', {



                'error_message': error_msg,



                'traceback': tb



            })



    



    return redirect('store:cart')





@login_required
def paystack_payment_redirect(request):
    """Display Paystack payment page"""
    order_id = request.session.get('pending_order_id')
    
    if not order_id:
        messages.error(request, 'No pending order found.')
        return redirect('store:cart')
    
    # Try to get PendingOrder first, then Order as fallback
    from .models import PendingOrder
    try:
        pending_order = PendingOrder.objects.get(id=order_id, user=request.user)
        
        # Create a temporary order-like object for PaystackPayment
        class TempOrder:
            def __init__(self, pending_order):
                self.id = str(pending_order.id)
                self.order_number = f'PENDING-{str(pending_order.id)[:8]}'
                self.total_amount = pending_order.total_amount
                self.email = pending_order.email
        
        temp_order = TempOrder(pending_order)
        paystack_payment = PaystackPayment(temp_order, request)
        payment_form = paystack_payment.get_payment_form()
        
        return render(request, 'store/paystack_payment.html', {
            'order': temp_order,
            'payment_form': payment_form,
            'paystack_public_key': paystack_payment.config.get_public_key()
        })
        
    except PendingOrder.DoesNotExist:
        # Try to get regular Order as fallback
        order = get_object_or_404(Order, id=order_id, user=request.user)
        paystack_payment = PaystackPayment(order, request)
        payment_form = paystack_payment.get_payment_form()
        
        return render(request, 'store/paystack_payment.html', {
            'order': order,
            'payment_form': payment_form,
            'paystack_public_key': paystack_payment.config.get_public_key()
        })


@login_required
def paystack_callback(request):
    """Handle Paystack payment callback"""
    reference = request.GET.get('reference')
    order_id = request.session.get('pending_order_id')
    
    if not reference or not order_id:
        messages.error(request, 'Invalid payment callback.')
        return redirect('store:cart')
    
    # Try to get PendingOrder first, then Order as fallback
    from .models import PendingOrder
    try:
        pending_order = PendingOrder.objects.get(id=order_id, user=request.user)
        
        # Create a temporary order-like object for PaystackPayment
        class TempOrder:
            def __init__(self, pending_order):
                self.id = str(pending_order.id)
                self.order_number = f'PENDING-{str(pending_order.id)[:8]}'
                self.total_amount = pending_order.total_amount
                self.email = pending_order.email
                self.payment_status = 'pending'
                self.status = 'pending_payment'
                
            def save(self):
                # Convert PendingOrder to actual Order on successful payment
                from .models import Order, OrderItem
                import uuid
                
                # Create actual Order from PendingOrder data
                actual_order = Order.objects.create(
                    id=uuid.uuid4(),
                    user=pending_order.user,
                    email=pending_order.email,
                    total_amount=pending_order.total_amount,
                    payment_status='completed',
                    status='paid',
                    shipping_street=pending_order.order_data.get('shipping_street', ''),
                    shipping_town=pending_order.order_data.get('shipping_town', ''),
                    shipping_city=pending_order.order_data.get('shipping_city', ''),
                    shipping_province=pending_order.order_data.get('shipping_province', ''),
                    shipping_postal=pending_order.order_data.get('shipping_postal', ''),
                    billing_street=pending_order.order_data.get('billing_street', ''),
                    billing_town=pending_order.order_data.get('billing_town', ''),
                    billing_city=pending_order.order_data.get('billing_city', ''),
                    billing_province=pending_order.order_data.get('billing_province', ''),
                    billing_postal=pending_order.order_data.get('billing_postal', ''),
                    phone=pending_order.order_data.get('phone', ''),
                    notes=pending_order.order_data.get('notes', '')
                )
                
                # Add order items
                for item_data in pending_order.order_data.get('cart_items', []):
                    from .models import iPhoneProduct
                    product = iPhoneProduct.objects.get(id=item_data['product_id'])
                    OrderItem.objects.create(
                        order=actual_order,
                        product=product,
                        quantity=item_data['quantity'],
                        price=item_data['price']
                    )
                
                # Delete the pending order
                pending_order.delete()
                
                # Store the actual order ID for redirect
                self.actual_order_id = actual_order.id
        
        temp_order = TempOrder(pending_order)
        result = process_paystack_callback(reference, temp_order)
        
        if result['success']:
            # Update order status and convert to actual order
            temp_order.payment_status = 'completed'
            temp_order.status = 'paid'
            temp_order.save()
            
            # Clear session
            if 'pending_order_id' in request.session:
                del request.session['pending_order_id']
            
            messages.success(request, 'Payment successful! Your order has been confirmed.')
            return redirect('store:order_detail', order_id=temp_order.actual_order_id)
        else:
            messages.error(request, f"Payment failed: {result['message']}")
            return redirect('store:payment_cancel')
            
    except PendingOrder.DoesNotExist:
        # Try to get regular Order as fallback
        order = get_object_or_404(Order, id=order_id, user=request.user)
        result = process_paystack_callback(reference, order)
        
        if result['success']:
            # Update order status
            order.payment_status = 'completed'
            order.status = 'paid'
            order.save()
            
            # Clear session
            if 'pending_order_id' in request.session:
                del request.session['pending_order_id']
            
            messages.success(request, 'Payment successful! Your order has been confirmed.')
            return redirect('store:order_detail', order_id=order.id)
        else:
            messages.error(request, f"Payment failed: {result['message']}")
            return redirect('store:payment_cancel')


@login_required



def checkout_debug(request):



    """Debug view to check checkout configuration"""



    from django.conf import settings



    import traceback



    



    debug_info = {



        'session_key': request.session.session_key,



        'user': str(request.user),



        'cart_exists': False,



        'cart_items_count': 0,



        'payfast_config': {



            'mode': getattr(settings, 'PAYFAST_MODE', 'NOT SET'),



            'merchant_id': getattr(settings, 'PAYFAST_MERCHANT_ID', 'NOT SET'),



            'merchant_key': getattr(settings, 'PAYFAST_MERCHANT_KEY', 'NOT SET')[:5] + '...' if getattr(settings, 'PAYFAST_MERCHANT_KEY', '') else 'NOT SET',



        },



        'errors': []



    }



    



    # Check cart



    try:



        if not request.session.session_key:



            request.session.create()



        cart = Cart.objects.get_or_create(session_key=request.session.session_key)[0]



        cart_items = cart.cartitem_set.all()



        debug_info['cart_exists'] = True



        debug_info['cart_items_count'] = cart_items.count()



        debug_info['cart_total'] = str(cart.get_total_price())



    except Exception as e:



        debug_info['errors'].append(f'Cart error: {str(e)}')



        debug_info['errors'].append(traceback.format_exc())



    



    # Check PayFast config



    try:



        from .payfast import PayFastConfig



        config = PayFastConfig()



        debug_info['payfast_config']['process_url'] = config.get_process_url()



        debug_info['payfast_config']['merchant_id'] = config.get_merchant_id()



    except Exception as e:



        debug_info['errors'].append(f'PayFast config error: {str(e)}')



        debug_info['errors'].append(traceback.format_exc())



    



    return JsonResponse(debug_info, json_dumps_params={'indent': 2})











@login_required



def payment_debug(request):



    """Debug view to check PayFast payment form data"""



    from django.conf import settings



    from .payfast import PayFastConfig, PayFastPayment



    from .models import Order



    import traceback



    



    order_id = request.session.get('pending_order_id')



    



    debug_info = {



        'payfast_mode': getattr(settings, 'PAYFAST_MODE', 'NOT SET'),



        'merchant_id': getattr(settings, 'PAYFAST_MERCHANT_ID', 'NOT SET'),



        'merchant_key': getattr(settings, 'PAYFAST_MERCHANT_KEY', 'NOT SET')[:5] + '...' if getattr(settings, 'PAYFAST_MERCHANT_KEY', '') else 'NOT SET',



        'process_url': '',



        'has_pending_order': bool(order_id),



        'payment_form_data': {},



        'errors': []



    }



    



    try:



        config = PayFastConfig()



        debug_info['process_url'] = config.get_process_url()



    except Exception as e:



        debug_info['errors'].append(f'Config error: {str(e)}')



    



    if order_id:



        try:



            order = Order.objects.get(id=order_id, user=request.user)



            payfast_payment = PayFastPayment(order, request)



            payment_form = payfast_payment.get_payment_form()



            debug_info['payment_form_data'] = payment_form



        except Exception as e:



            debug_info['errors'].append(f'Payment form error: {str(e)}')



            debug_info['errors'].append(traceback.format_exc())



    



    return JsonResponse(debug_info, json_dumps_params={'indent': 2})











@login_required



def payment_redirect(request):



    """Display payment redirect page with auto-submitting form"""



    order_id = request.session.get('pending_order_id')



    if not order_id:



        messages.error(request, 'No pending order found.')



        return redirect('store:cart')



    



    order = get_object_or_404(Order, id=order_id, user=request.user)



    payfast_payment = PayFastPayment(order, request)



    payment_form = payfast_payment.get_payment_form()



    



    return render(request, 'store/payment_redirect.html', {



        'order': order,



        'payment_form': payment_form



    })











@csrf_exempt



def payment_notify(request):



    """



    PayFast ITN (Instant Transaction Notification) handler



    This is called by PayFast server-to-server when payment is complete



    """



    if request.method != 'POST':



        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})



    



    try:



        # Get POST data



        data = request.POST.dict()



        



        # Verify signature



        signature = data.pop('signature', None)



        if not signature:



            return JsonResponse({'status': 'error', 'message': 'Missing signature'})



        



        if not verify_payfast_signature(data, signature):



            return JsonResponse({'status': 'error', 'message': 'Invalid signature'})



        



        # Handle payment status



        payment_status = data.get('payment_status', '').lower()



        



        if payment_status == 'complete':
            # Create order after successful payment using PendingOrder data
            
            from .models import PendingOrder
            
            # Get pending order using m_payment_id
            pending_order_id = data.get('m_payment_id')
            
            try:
                pending_order = PendingOrder.objects.get(id=pending_order_id, is_processed=False)
                order_data = pending_order.order_data
                
                # Create the actual order
                order = Order.objects.create(
                    user=pending_order.user,
                    total_amount=pending_order.total_amount,
                    shipping_street=order_data['shipping_street'],
                    shipping_town=order_data['shipping_town'],
                    shipping_city=order_data['shipping_city'],
                    shipping_province=order_data['shipping_province'],
                    shipping_postal=order_data['shipping_postal'],
                    billing_street=order_data['billing_street'],
                    billing_town=order_data['billing_town'],
                    billing_city=order_data['billing_city'],
                    billing_province=order_data['billing_province'],
                    billing_postal=order_data['billing_postal'],
                    shipping_address=order_data['shipping_address'],
                    billing_address=order_data['billing_address'],
                    email=order_data['email'],
                    phone=order_data['phone'],
                    notes=order_data['notes'],
                    status='processing',
                    payment_status='completed',
                    pf_payment_id=data.get('pf_payment_id'),
                    pf_transaction_id=data.get('pf_transaction_id'),
                    pf_payment_status=data.get('payment_status'),
                    pf_amount_gross=data.get('amount_gross'),
                    pf_amount_fee=data.get('amount_fee'),
                    pf_amount_net=data.get('amount_net'),
                    pf_payment_date=datetime.now()
                )
                
                # Create order items
                for item_data in order_data['cart_items']:
                    from .models import iPhoneProduct, OrderItem
                    product = iPhoneProduct.objects.get(id=item_data['product_id'])
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item_data['quantity'],
                        price=item_data['price']
                    )
                    # Update stock
                    product.stock_quantity -= item_data['quantity']
                    product.save()
                
                # Mark pending order as processed
                pending_order.is_processed = True
                pending_order.save()

                
            except PendingOrder.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Pending order not found or already processed'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Error creating order: {str(e)}'})



        elif payment_status == 'failed':

            order = Order.objects.get(id=data.get('m_payment_id'))
            order.payment_status = 'failed'
            order.save()

        elif payment_status == 'cancelled':

            order = Order.objects.get(id=data.get('m_payment_id'))
            order.payment_status = 'cancelled'
            order.save()

        



        return JsonResponse({'status': 'ok'})



        



    except Exception as e:



        return JsonResponse({'status': 'error', 'message': str(e)})











@login_required



def payment_success(request):



    """Customer is redirected here after successful payment"""



    order_id = request.session.get('pending_order_id')



    



    if order_id:



        try:



            order = Order.objects.get(id=order_id, user=request.user)



            # Clear pending order from session



            del request.session['pending_order_id']



            request.session.modified = True



            



            messages.success(request, f'Payment successful! Order number: {order.order_number}')



            return redirect('store:order_detail', order_id=order.id)



        except Order.DoesNotExist:



            pass



    



    messages.success(request, 'Payment completed successfully!')



    return redirect('store:order_list')











@login_required



def payment_cancel(request):



    """Customer is redirected here if they cancel payment"""



    order_id = request.session.get('pending_order_id')



    



    if order_id:



        try:



            order = Order.objects.get(id=order_id, user=request.user)



            order.payment_status = 'cancelled'



            order.save()



            



            # Restore stock



            for item in order.get_items():



                item.product.stock_quantity += item.quantity



                item.product.save()



            



            messages.warning(request, 'Payment was cancelled. Your order has been saved but not processed.')



        except Order.DoesNotExist:



            messages.warning(request, 'Payment was cancelled.')



    else:



        messages.warning(request, 'Payment was cancelled.')



    



    return redirect('store:cart')















@login_required







def order_list(request):







    orders = Order.objects.filter(user=request.user).order_by('-created_at')







    return render(request, 'store/order_list.html', {'orders': orders})












def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Render order detail page
    return render(request, 'store/order_detail.html', {
        'order': order,
        'manual_payment': {
            'bank_name': settings.ORDER_PAYMENT_BANK_NAME,
            'account_name': settings.ORDER_PAYMENT_ACCOUNT_NAME,
            'account_number': settings.ORDER_PAYMENT_ACCOUNT_NUMBER,
            'branch_code': settings.ORDER_PAYMENT_BRANCH_CODE,
            'account_type': settings.ORDER_PAYMENT_ACCOUNT_TYPE,
            'proof_email': settings.ORDER_PAYMENT_PROOF_EMAIL,
            'whatsapp': settings.ORDER_PAYMENT_WHATSAPP,
        }
    })


