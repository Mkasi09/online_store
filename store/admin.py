from django.contrib import admin

from .models import iPhoneModel, Color, iPhoneProduct, Cart, CartItem, Order, OrderItem



@admin.register(iPhoneModel)

class iPhoneModelAdmin(admin.ModelAdmin):

    list_display = ['name', 'release_year', 'display_size', 'storage_options']

    list_filter = ['release_year']

    search_fields = ['name', 'description']

    ordering = ['-release_year', 'name']



@admin.register(Color)

class ColorAdmin(admin.ModelAdmin):

    list_display = ['name', 'hex_code']

    search_fields = ['name']

    ordering = ['name']



@admin.register(iPhoneProduct)

class iPhoneProductAdmin(admin.ModelAdmin):

    list_display = ['iphone_model', 'color', 'storage', 'condition', 'grade', 'price', 'stock_quantity', 'is_active', 'cover_photo_thumbnail']

    list_filter = ['iphone_model', 'color', 'storage', 'condition', 'grade', 'is_active']

    search_fields = ['iphone_model__name', 'color__name']

    list_editable = ['price', 'stock_quantity', 'is_active']

    ordering = ['-created_at']

    

    # Add JavaScript for auto price calculation
    class Media:
        js = ('admin/js/iphone_price.js',)

    

    fieldsets = (

        ('Product Information', {

            'fields': ('iphone_model', 'color', 'storage', 'condition', 'grade')

        }),

        ('Pricing & Inventory', {

            'fields': ('price', 'stock_quantity', 'is_active')

        }),

        ('Product Images', {

            'fields': ('image', 'cover_photo'),

            'description': 'Upload product images. Cover photo will be used as the main image in product listings.'

        }),

    )

    

    def cover_photo_thumbnail(self, obj):

        if obj.cover_photo:

            return f'<img src="{obj.cover_photo.url}" width="50" height="50" style="object-fit: cover;" />'

        elif obj.image:

            return f'<img src="{obj.image.url}" width="50" height="50" style="object-fit: cover;" />'

        return "No Image"

    cover_photo_thumbnail.short_description = 'Cover Photo'

    cover_photo_thumbnail.allow_tags = True



@admin.register(Cart)

class CartAdmin(admin.ModelAdmin):

    list_display = ['session_key', 'created_at', 'updated_at']

    readonly_fields = ['session_key', 'created_at', 'updated_at']

    ordering = ['-created_at']



@admin.register(CartItem)

class CartItemAdmin(admin.ModelAdmin):

    list_display = ['cart', 'product', 'quantity', 'added_at']

    list_filter = ['added_at', 'product__iphone_model']

    search_fields = ['product__iphone_model__name', 'cart__session_key']

    ordering = ['-added_at']



class OrderItemInline(admin.TabularInline):

    model = OrderItem

    extra = 0

    readonly_fields = ['product', 'quantity', 'price']



@admin.register(Order)

class OrderAdmin(admin.ModelAdmin):

    list_display = ['order_number', 'user_info', 'email', 'status_progress', 'payment_status_badge', 'total_amount', 'created_at']

    list_filter = ['status', 'payment_status', 'created_at']

    search_fields = ['id', 'email', 'phone', 'user__username', 'user__email', 'order_number']

    readonly_fields = ['id', 'created_at', 'updated_at', 'order_number']

    inlines = [OrderItemInline]

    ordering = ['-created_at']

    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']

    list_per_page = 25

    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def user_info(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name() or obj.user.username}"
        return "Guest User"
    user_info.short_description = 'Customer'

    def status_progress(self, obj):
        status_colors = {
            'pending_payment': '#ffc107',
            'processing': '#17a2b8', 
            'shipped': '#6f42c1',
            'delivered': '#28a745',
            'cancelled': '#dc3545'
        }
        
        progress_steps = [
            ('pending_payment', 'Payment'),
            ('processing', 'Processing'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered')
        ]
        
        current_step_index = 0
        for i, (status, label) in enumerate(progress_steps):
            if obj.status == status:
                current_step_index = i
                break
            elif obj.status == 'cancelled':
                current_step_index = -1
                break
        
        if obj.status == 'cancelled':
            return '<span style="color: #dc3545; font-weight: bold;">❌ Cancelled</span>'
        
        progress_html = '<div style="display: flex; align-items: center; gap: 5px;">'
        
        for i, (status, label) in enumerate(progress_steps):
            if i <= current_step_index:
                progress_html += f'<span style="color: {status_colors.get(status, "#6c757d")};">●</span>'
            else:
                progress_html += '<span style="color: #dee2e6;">○</span>'
            
            if i == current_step_index:
                progress_html += f'<strong style="color: {status_colors.get(status, "#6c757d")};">{label}</strong>'
            elif i < current_step_index:
                progress_html += f'<span style="color: #28a745;">{label}</span>'
            else:
                progress_html += f'<span style="color: #adb5bd;">{label}</span>'
                
            if i < len(progress_steps) - 1:
                progress_html += ' → '
        
        progress_html += '</div>'
        return progress_html
    status_progress.short_description = 'Order Progress'
    status_progress.allow_tags = True

    def payment_status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'completed': '#28a745', 
            'failed': '#dc3545',
            'cancelled': '#6c757d'
        }
        color = colors.get(obj.payment_status, '#6c757d')
        return f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">{obj.get_payment_status_display()}</span>'
    payment_status_badge.short_description = 'Payment'
    payment_status_badge.allow_tags = True

    # Custom Actions
    def mark_as_processing(self, request, queryset):
        updated = queryset.filter(status='pending_payment').update(status='processing')
        self.message_user(request, f'{updated} orders marked as processing.')
    mark_as_processing.short_description = 'Mark selected orders as Processing'

    def mark_as_shipped(self, request, queryset):
        updated = queryset.filter(status='processing').update(status='shipped')
        self.message_user(request, f'{updated} orders marked as shipped.')
    mark_as_shipped.short_description = 'Mark selected orders as Shipped'

    def mark_as_delivered(self, request, queryset):
        updated = queryset.filter(status='shipped').update(status='delivered')
        self.message_user(request, f'{updated} orders marked as delivered.')
    mark_as_delivered.short_description = 'Mark selected orders as Delivered'

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.exclude(status='delivered').update(status='cancelled')
        self.message_user(request, f'{updated} orders marked as cancelled.')
    mark_as_cancelled.short_description = 'Mark selected orders as Cancelled'

    fieldsets = (

        ('Order Information', {

            'fields': ('order_number', 'user', 'status', 'payment_status', 'total_amount', 'created_at')

        }),

        ('Payment Details', {

            'fields': ('pf_payment_id', 'pf_payment_status', 'pf_amount_gross', 'pf_amount_fee', 'pf_amount_net', 'pf_payment_date'),

            'classes': ('collapse',)

        }),

        ('Shipping Address', {

            'fields': ('shipping_street', 'shipping_town', 'shipping_city', 'shipping_province', 'shipping_postal', 'shipping_address')

        }),

        ('Billing Address', {

            'fields': ('billing_street', 'billing_town', 'billing_city', 'billing_province', 'billing_postal', 'billing_address')

        }),

        ('Contact Information', {

            'fields': ('email', 'phone')

        }),

        ('Additional Information', {

            'fields': ('notes', 'updated_at')

        }),

    )



