import random
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from iphonestore.settings import BASE_DIR, _database_config, _email_config
from store.management.commands.populate_iphones import Command
from store.discounts import InvalidDiscountCode, calculate_checkout_discount
from store.models import (
    Cart,
    CartItem,
    Color,
    Order,
    OrderItem,
    iPhoneModel,
    iPhoneProduct,
    ProductReview,
)


class DatabaseConfigurationTests(SimpleTestCase):
    def test_missing_database_url_keeps_existing_sqlite_database(self):
        for database_url in (None, ''):
            with self.subTest(database_url=database_url):
                database = _database_config(database_url)['default']

                self.assertEqual(database['ENGINE'], 'django.db.backends.sqlite3')
                self.assertEqual(database['NAME'], BASE_DIR / 'db.sqlite3')

    def test_postgresql_database_url_is_parsed_without_connecting(self):
        database = _database_config(
            'postgresql://store_user:p%40ssword@db.example.test:5432/online_store'
            '?sslmode=require'
        )['default']

        self.assertEqual(database['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(database['NAME'], 'online_store')
        self.assertEqual(database['USER'], 'store_user')
        self.assertEqual(database['PASSWORD'], 'p@ssword')
        self.assertEqual(database['HOST'], 'db.example.test')
        self.assertEqual(database['PORT'], 5432)
        self.assertEqual(database['OPTIONS']['sslmode'], 'require')
        self.assertEqual(database['CONN_MAX_AGE'], 600)


class EmailConfigurationTests(SimpleTestCase):
    def test_gmail_defaults_do_not_include_a_password(self):
        email = _email_config({})

        self.assertEqual(email['host'], 'smtp.gmail.com')
        self.assertEqual(email['port'], 587)
        self.assertTrue(email['use_tls'])
        self.assertEqual(email['user'], 'iphonestorequaries@gmail.com')
        self.assertEqual(email['password'], '')

    def test_email_settings_can_be_overridden_from_environment(self):
        email = _email_config({
            'EMAIL_HOST': 'smtp.example.test',
            'EMAIL_PORT': '465',
            'EMAIL_USE_TLS': 'false',
            'EMAIL_HOST_USER': 'mail@example.test',
            'EMAIL_HOST_PASSWORD': 'configured-secret',
        })

        self.assertEqual(email, {
            'host': 'smtp.example.test',
            'port': 465,
            'use_tls': False,
            'user': 'mail@example.test',
            'password': 'configured-secret',
        })

    def test_invalid_tls_value_is_rejected(self):
        with self.assertRaisesMessage(ValueError, 'EMAIL_USE_TLS must be a boolean value.'):
            _email_config({'EMAIL_USE_TLS': 'sometimes'})


class CatalogReplacementTests(TestCase):
    def test_new_price_rounds_to_nearest_whole_rand(self):
        self.assertEqual(Command.new_price_from_grade_a(1005), 1307)
        self.assertEqual(Command.discount_price(1005), 800)
        self.assertEqual(Command.discount_price(1799), 1400)
        self.assertEqual(Command.discount_price(Command.new_price_from_grade_a(6499)), 6800)

    def test_round_to_nearest_hundred_uses_half_up(self):
        self.assertEqual(Command.round_to_nearest_hundred(2799), 2800)
        self.assertEqual(Command.round_to_nearest_hundred(2790), 2800)
        self.assertEqual(Command.round_to_nearest_hundred(2749), 2700)
        self.assertEqual(Command.round_to_nearest_hundred(8527), 8500)

    def setUp(self):
        model = iPhoneModel.objects.create(
            name='iPhone X',
            release_year=2017,
            display_size='5.8 inches',
            storage_options='64GB',
        )
        color = Color.objects.create(name='Black', hex_code='#000000')
        product = iPhoneProduct.objects.create(
            iphone_model=model,
            color=color,
            storage='64GB',
            condition='used',
            grade='A',
            price=100,
            stock_quantity=1,
        )
        order = Order.objects.create(total_amount=200, email='buyer@example.com')
        self.order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=2,
            price=100,
        )
        cart = Cart.objects.create(session_key='catalog-reset-test')
        CartItem.objects.create(cart=cart, product=product)

    def test_reset_requires_explicit_confirmation(self):
        with self.assertRaises(CommandError):
            call_command('populate_iphones')
        self.assertEqual(iPhoneProduct.objects.count(), 1)

    def test_sync_adds_models_without_resetting_stock_carts_or_orders(self):
        order_product_id = self.order_item.product_id
        call_command('populate_iphones', sync=True, verbosity=0)

        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.product_id, order_product_id)
        self.assertEqual(self.order_item.price, Decimal('100.00'))
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(self.order_item.product.stock_quantity, 1)
        self.assertEqual(self.order_item.product.price, Decimal('2800.00'))
        self.assertEqual(set(iPhoneModel.objects.values_list('name', flat=True)), set(Command.CATALOG))

        new_pro = iPhoneProduct.objects.get(
            iphone_model__name='iPhone 13 Pro',
            color__name='Graphite',
            storage='256GB',
            condition='new',
            grade__isnull=True,
        )
        self.assertEqual(new_pro.price, Decimal('8500.00'))
        self.assertTrue(new_pro.image_url.endswith('/Graphite.png'))
        self.assertTrue(
            iPhoneProduct.objects.filter(
                iphone_model__name='iPhone 13 Pro',
                storage='256GB',
                condition='used',
                grade='A',
            ).exists()
        )
        home = self.client.get(reverse('store:home'))
        self.assertContains(home, 'iPhone 13 Pro')
        self.assertNotContains(home, 'View Refurbished')
        self.assertNotContains(home, '?condition=refurbished')

        product_count = iPhoneProduct.objects.count()
        call_command('populate_iphones', sync=True, verbosity=0)
        self.assertEqual(iPhoneProduct.objects.count(), product_count)
        new_pro.refresh_from_db()
        self.assertEqual(new_pro.price, Decimal('8500.00'))

    def test_reset_creates_exact_variants_and_preserves_order_lines(self):
        call_command('populate_iphones', confirm_reset=True, verbosity=0)

        products = list(iPhoneProduct.objects.select_related('iphone_model', 'color'))
        self.assertEqual(len(products), 550)
        self.assertEqual(
            {condition: sum(product.condition == condition for product in products)
             for condition in Command.INVENTORY_COUNTS},
            Command.INVENTORY_COUNTS,
        )
        for product in products:
            data = Command.CATALOG[product.iphone_model.name]
            if product.condition == 'new':
                self.assertIsNone(product.grade)
                expected_price = Command.discount_price(
                    Command.new_price_from_grade_a(data['prices'][product.storage][0])
                )
            else:
                self.assertIsNotNone(product.grade)
                expected_price = Command.discount_price(
                    data['prices'][product.storage][Command.GRADES.index(product.grade)]
                )
            self.assertEqual(
                int(product.price),
                expected_price,
            )
            self.assertEqual(int(product.price) % 100, 0)
        new_models = {
            product.iphone_model.name for product in products if product.condition == 'new'
        }
        self.assertTrue(new_models)
        self.assertTrue(new_models.issubset(Command.NEW_MODELS))
        self.assertFalse(
            iPhoneProduct.objects.filter(condition='new', iphone_model__name__in=[
                'iPhone 7', 'iPhone 8', 'iPhone X', 'iPhone XR', 'iPhone 11', 'iPhone 12',
            ]).exists()
        )
        self.assertFalse(iPhoneProduct.objects.filter(condition='refurbished').exists())
        self.assertEqual(
            set(iPhoneModel.objects.values_list('name', flat=True)),
            set(Command.CATALOG),
        )
        self.assertEqual(
            set(Color.objects.values_list('name', flat=True)),
            {color for data in Command.CATALOG.values() for color in data['colors']},
        )
        self.assertEqual(iPhoneModel.objects.count(), 23)
        self.assertFalse(iPhoneModel.objects.filter(name='iPhone 18').exists())
        self.assertFalse(
            iPhoneProduct.objects.filter(
                iphone_model__name='iPhone 18 Pro Max',
                storage__in=('1TB', '2TB'),
            ).exists()
        )
        for model_name in Command.NEW_MODELS:
            for condition in ('new', 'used'):
                self.assertTrue(
                    iPhoneProduct.objects.filter(
                        iphone_model__name=model_name,
                        condition=condition,
                    ).exists(),
                    f'{model_name} should have {condition} listings',
                )
        for model_name in Command.CATALOG:
            for storage in Command.CATALOG[model_name]['storage']:
                self.assertTrue(
                    iPhoneModel.objects.filter(
                        name=model_name,
                        storage_options__contains=storage,
                    ).exists()
                )
        self.assertEqual(set(iPhoneProduct.objects.values_list('stock_quantity', flat=True)), {0, 2, 5, 10})
        for condition in Command.INVENTORY_COUNTS:
            stock = set(iPhoneProduct.objects.filter(condition=condition).values_list('stock_quantity', flat=True))
            self.assertTrue({0, 2, 5, 10}.issubset(stock))
        self.assertEqual(CartItem.objects.count(), 0)

        self.order_item.refresh_from_db()
        self.assertIsNone(self.order_item.product)
        self.assertEqual(self.order_item.product_name, 'iPhone X')
        self.assertEqual(self.order_item.product_color, 'Black')
        self.assertEqual(self.order_item.product_storage, '64GB')
        self.assertEqual(self.order_item.product_grade, 'A')

        for product in iPhoneProduct.objects.select_related('iphone_model'):
            if product.iphone_model.name.startswith('iPhone 18'):
                expected_image = Command.LOCAL_IMAGE_FILES[product.iphone_model.name][product.color.name]
                self.assertEqual(product.image.name, expected_image)
                self.assertEqual(product.image_url, '')
            else:
                self.assertTrue(product.image_url.startswith('https://img.appledb.dev/device@256/'))
                self.assertFalse(product.image.name)
            self.assertFalse(product.cover_photo.name)

        for color in ('Jet Black', 'Gold'):
            selected = iPhoneProduct.objects.filter(
                iphone_model__name='iPhone 7',
                color__name=color,
                condition='used',
            ).first()
            self.assertIsNotNone(selected)
            response = self.client.get(selected.get_absolute_url())
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, selected.image_url)
            self.assertContains(response, 'Select Grade:')

        self.assertEqual(
            Command().get_product_image('iPhone 8', 'Space Grey'),
            'https://img.appledb.dev/device@256/iPhone10,1/Space%20Gray.png',
        )
        self.assertEqual(
            Command().get_product_image('iPhone 7', 'Red'),
            'https://img.appledb.dev/device@256/iPhone9,1/%28PRODUCT%29RED.png',
        )
        self.assertEqual(
            Command().get_product_image('iPhone 13 Pro', 'Graphite'),
            'https://img.appledb.dev/device@256/iPhone14,2/Graphite.png',
        )
        self.assertEqual(Command().get_product_image('iPhone 7', 'Coral'), '')
        self.assertEqual(Command().get_product_image('iPhone 18 Pro', 'Black Titanium'), '')
        self.assertEqual(
            Command().get_product_local_image('iPhone 18 Pro', 'Black Titanium'),
            'iphone_images/iphone_18_black.png',
        )
        self.assertEqual(
            Command().get_product_local_image('iPhone 18 Pro Max', 'Desert Titanium'),
            'iphone_images/iphone_18_desert.png',
        )
        self.assertEqual(
            Command().get_product_local_image('iPhone 18 Pro Max', 'Natural Titanium'),
            'iphone_images/iphone_18_natural.png',
        )
        self.assertEqual(
            Command().get_product_local_image('iPhone 18 Pro Max', 'White Titanium'),
            'iphone_images/iphone_18_white.png',
        )

        iphone_18 = iPhoneModel.objects.get(name='iPhone 18 Pro')
        self.assertIsNone(iphone_18.release_year)
        self.assertNotIn('Placeholder', iphone_18.description)
        self.assertNotIn('placeholder', iphone_18.description)
        self.assertNotIn('unverified', iphone_18.description)
        for model_name, image_map in Command.LOCAL_IMAGE_FILES.items():
            for color_name, image_path in image_map.items():
                product = iPhoneProduct.objects.filter(
                    iphone_model__name=model_name,
                    color__name=color_name,
                ).first()
                self.assertIsNotNone(product)
                response = self.client.get(product.get_absolute_url())
                self.assertNotContains(response, 'Placeholder catalog entry')
                self.assertNotContains(response, 'supplied local color asset')
                self.assertNotContains(response, 'unverified official iPhone 18 imagery')
                self.assertContains(response, f'/media/{image_path}')
                self.assertTrue(product.image.storage.exists(image_path))


class ProductListOrderingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        color = Color.objects.create(name='Black', hex_code='#111111')
        model_names = [
            'iPhone 7', 'iPhone 8', 'iPhone X', 'iPhone XR', 'iPhone 11',
            'iPhone 12', 'iPhone 13', 'iPhone 14', 'iPhone 15', 'iPhone 16',
            'iPhone 17', 'iPhone 18 Pro', 'iPhone 18 Pro Max',
        ]
        cls.product_ids = []
        for index, name in enumerate(model_names, start=1):
            model = iPhoneModel.objects.create(
                name=name,
                release_year=2010 + index,
                display_size='6.1 inches',
                storage_options='128GB',
            )
            product = iPhoneProduct.objects.create(
                iphone_model=model,
                color=color,
                storage='128GB',
                condition='used',
                grade='A',
                price=index * 100,
                stock_quantity=1,
            )
            cls.product_ids.append(product.pk)

    def test_unfiltered_catalog_shuffles_consistently_across_pages(self):
        url = reverse('store:product_list')
        first_page = self.client.get(url)
        self.assertEqual(first_page.context['current_sort'], 'shuffle')
        shuffle_seed = first_page.context['shuffle_seed']
        self.assertRegex(shuffle_seed, r'^[0-9a-f]{16}$')
        self.assertIn(f'shuffle={shuffle_seed}', first_page.context['pagination_query'])

        page_two = self.client.get(
            url,
            {'page': 2, 'shuffle': shuffle_seed},
        )
        actual_order = [
            product.pk
            for response in (first_page, page_two)
            for product in response.context['products']
        ]
        expected_order = list(
            iPhoneProduct.objects.filter(is_active=True)
            .order_by('-created_at', '-pk')
            .values_list('pk', flat=True)
        )
        random.Random(int(shuffle_seed, 16)).shuffle(expected_order)

        self.assertEqual(actual_order, expected_order)
        self.assertEqual(len(actual_order), len(set(actual_order)))

    def test_filtered_and_explicitly_sorted_catalogs_keep_their_order(self):
        url = reverse('store:product_list')
        filtered = self.client.get(url, {'condition': 'used', 'sort': 'shuffle'})
        self.assertEqual(filtered.context['current_sort'], 'newest')
        self.assertFalse(filtered.context['shuffle_seed'])
        self.assertNotContains(filtered, '<option value="shuffle"')
        self.assertEqual(
            {product.condition for product in filtered.context['products']},
            {'used'},
        )

        price_sorted = self.client.get(url, {'sort': 'price_low'})
        prices = [product.price for product in price_sorted.context['products']]
        self.assertEqual(prices, sorted(prices))
        self.assertEqual(price_sorted.context['current_sort'], 'price_low')
        self.assertFalse(price_sorted.context['shuffle_seed'])
        self.assertContains(price_sorted, 'iPhone 7 to iPhone 18')

    def test_pagination_always_shows_navigation_and_preserves_filters(self):
        model = iPhoneModel.objects.get(name='iPhone 7')
        for index in range(12):
            color = Color.objects.create(
                name=f'Pager Color {index}',
                hex_code='#123456',
            )
            iPhoneProduct.objects.create(
                iphone_model=model,
                color=color,
                storage='128GB',
                condition='used',
                grade='A',
                price=10000 + index,
                stock_quantity=1,
            )

        url = reverse('store:product_list')
        filters = {'condition': 'used', 'sort': 'price_low'}
        first = self.client.get(url, filters)
        self.assertEqual(first.context['page_obj'].number, 1)
        self.assertEqual(first.context['page_numbers'], [1, 2, 3])
        self.assertContains(first, 'Previous')
        self.assertContains(first, 'Next')
        self.assertContains(first, 'aria-disabled="true"')
        self.assertContains(first, 'page=2')
        self.assertIn('condition=used', first.context['pagination_query'])
        self.assertIn('sort=price_low', first.context['pagination_query'])

        middle = self.client.get(url, {**filters, 'page': 2})
        self.assertEqual(middle.context['page_obj'].number, 2)
        self.assertEqual(middle.context['page_numbers'], [1, 2, 3])
        self.assertContains(middle, 'page=1')
        self.assertContains(middle, 'page=3')
        self.assertIn('condition=used', middle.context['pagination_query'])
        self.assertIn('sort=price_low', middle.context['pagination_query'])

        last = self.client.get(url, {**filters, 'page': 3})
        self.assertEqual(last.context['page_obj'].number, 3)
        self.assertFalse(last.context['page_obj'].has_next())
        self.assertEqual(last.context['page_numbers'], [1, 2, 3])
        self.assertContains(last, 'page=2')
        self.assertIn('condition=used', last.context['pagination_query'])
        self.assertIn('sort=price_low', last.context['pagination_query'])
        self.assertContains(last, 'aria-disabled="true"')


class CheckoutDiscountTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='buyer', password='test-password')
        self.client.force_login(user)
        session = self.client.session
        self.cart = Cart.objects.create(session_key=session.session_key)
        model = iPhoneModel.objects.create(
            name='iPhone 13',
            release_year=2021,
            display_size='6.1 inches',
            storage_options='128GB',
        )
        color = Color.objects.create(name='Midnight', hex_code='#222838')
        self.product = iPhoneProduct.objects.create(
            iphone_model=model,
            color=color,
            storage='128GB',
            condition='new',
            grade='A',
            price=1000,
            stock_quantity=5,
        )
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        self.checkout_data = {
            'shipping_street': '1 Main Street',
            'shipping_town': 'Sandton',
            'shipping_city': 'Johannesburg',
            'shipping_province': 'Gauteng',
            'shipping_postal': '2196',
            'billing_street': '1 Main Street',
            'billing_town': 'Sandton',
            'billing_city': 'Johannesburg',
            'billing_province': 'Gauteng',
            'billing_postal': '2196',
            'email': 'buyer@example.com',
        }

    def test_cart_checkout_form_shows_configured_discount_code(self):
        response = self.client.get(reverse('store:cart'))

        self.assertContains(response, 'Discount code')
        self.assertContains(response, 'PLUG20 (20% off through 31 December 2026)')
        self.assertContains(response, 'Save 20%')
        self.assertContains(response, 'id="sameAsShipping" name="same_as_shipping" checked')
        self.assertContains(response, 'alert alert-success border-success text-dark')

    def test_cart_applies_discount_and_displays_updated_total(self):
        response = self.client.post(
            reverse('store:cart'),
            {'discount_code': ' plug20 '},
        )
        self.assertRedirects(response, reverse('store:cart'))

        response = self.client.get(reverse('store:cart'))
        self.assertContains(response, 'Discount (PLUG20)')
        self.assertContains(response, '-R400.00')
        self.assertContains(response, 'R1600.00')
        self.assertEqual(
            self.client.session['cart_discount_code'],
            'PLUG20',
        )

    def test_cart_rejects_invalid_code_and_empty_code_clears_discount(self):
        self.client.post(reverse('store:cart'), {'discount_code': 'PLUG20'})
        response = self.client.post(
            reverse('store:cart'),
            {'discount_code': 'NOT-A-CODE'},
        )
        self.assertRedirects(response, reverse('store:cart'))
        self.assertEqual(
            self.client.session.get('cart_discount_code'),
            'PLUG20',
        )

        response = self.client.post(reverse('store:cart'), {'discount_code': ''})
        self.assertRedirects(response, reverse('store:cart'))
        self.assertNotIn('cart_discount_code', self.client.session)

    @patch('store.views.send_manual_payment_email', return_value=True)
    def test_checkout_applies_discount_to_order_total(self, send_email):
        self.client.post(reverse('store:cart'), {'discount_code': ' plug20 '})
        response = self.client.post(
            reverse('store:checkout'),
            self.checkout_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        order = Order.objects.get()
        self.assertEqual(order.subtotal_amount, Decimal('2000.00'))
        self.assertEqual(order.discount_code, 'PLUG20')
        self.assertEqual(order.discount_amount, Decimal('400.00'))
        self.assertEqual(order.total_amount, Decimal('1600.00'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)
        self.assertFalse(self.cart.cartitem_set.exists())
        send_email.assert_called_once()

    def test_invalid_code_does_not_create_order_or_decrement_stock(self):
        response = self.client.post(
            reverse('store:cart'),
            {'discount_code': 'NOT-A-CODE'},
        )
        self.assertRedirects(response, reverse('store:cart'))
        self.assertNotIn('cart_discount_code', self.client.session)
        self.assertFalse(Order.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5)

    def test_discount_cannot_be_applied_to_an_empty_order(self):
        self.cart.cartitem_set.all().delete()
        response = self.client.post(
            reverse('store:checkout'),
            {**self.checkout_data, 'discount_code': 'PLUG20'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertFalse(response.json()['success'])
        self.assertIn('empty', response.json()['error'])
        self.assertFalse(Order.objects.exists())

    @override_settings(CHECKOUT_DISCOUNT_CODES={
        'FREE': {'percent': 100, 'valid_until': date(2099, 12, 31)},
    })
    def test_discount_is_capped_at_subtotal(self):
        code, discount, total = calculate_checkout_discount(Decimal('12.50'), 'FREE')

        self.assertEqual(code, 'FREE')
        self.assertEqual(discount, Decimal('12.50'))
        self.assertEqual(total, Decimal('0.00'))
        with self.assertRaises(InvalidDiscountCode):
            calculate_checkout_discount(Decimal('0.00'), 'FREE')

    def test_promo_expires_after_31_december_2026(self):
        with patch('store.discounts.timezone.localdate', return_value=date(2026, 12, 31)):
            _, discount, total = calculate_checkout_discount(Decimal('100.00'), 'PLUG20')
        self.assertEqual(discount, Decimal('20.00'))
        self.assertEqual(total, Decimal('80.00'))

        with patch('store.discounts.timezone.localdate', return_value=date(2027, 1, 1)):
            with self.assertRaises(InvalidDiscountCode):
                calculate_checkout_discount(Decimal('100.00'), 'PLUG20')


class ProductReviewTests(TestCase):
    def setUp(self):
        self.model = iPhoneModel.objects.create(
            name='iPhone 13',
            release_year=2021,
            display_size='6.1 inches',
            storage_options='128GB',
        )
        self.color = Color.objects.create(name='Midnight', hex_code='#222838')
        self.product = iPhoneProduct.objects.create(
            iphone_model=self.model,
            color=self.color,
            storage='128GB',
            condition='used',
            grade='A',
            price=5200,
            stock_quantity=2,
        )
        self.user = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='test-password',
            first_name='Real',
            last_name='Customer',
        )
        self.url = reverse('store:submit_product_review', args=[self.product.pk])

    def test_anonymous_submission_requires_login(self):
        response = self.client.post(self.url, {'rating': 5, 'comment': 'Excellent phone and fast delivery'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        self.assertFalse(ProductReview.objects.exists())

    def test_authenticated_submission_is_pending_and_duplicate_is_blocked(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {'rating': 4, 'comment': 'Excellent phone and fast delivery'},
        )
        self.assertRedirects(response, self.product.get_absolute_url())
        review = ProductReview.objects.get()
        self.assertEqual(review.status, 'pending')
        self.assertFalse(review.verified_purchase)

        response = self.client.post(
            self.url,
            {'rating': 5, 'comment': 'Another review that should be rejected'},
        )
        self.assertRedirects(response, self.product.get_absolute_url())
        self.assertEqual(ProductReview.objects.count(), 1)

    def test_completed_purchase_marks_review_verified_and_only_approved_reviews_are_public(self):
        order = Order.objects.create(
            user=self.user,
            payment_status='completed',
            status='delivered',
            total_amount=5200,
            subtotal_amount=5200,
            email='reviewer@example.com',
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=5200,
        )
        self.client.force_login(self.user)
        self.client.post(
            self.url,
            {'rating': 5, 'comment': 'This phone arrived in excellent condition'},
        )
        review = ProductReview.objects.get()
        self.assertTrue(review.verified_purchase)

        detail = self.client.get(self.product.get_absolute_url())
        self.assertEqual(detail.context['review_summary']['review_count'], 0)
        self.assertContains(detail, 'No approved reviews yet')

        review.status = 'approved'
        review.save(update_fields=['status'])
        detail = self.client.get(self.product.get_absolute_url())
        self.assertEqual(detail.context['review_summary']['review_count'], 1)
        self.assertEqual(detail.context['review_summary']['average_rating'], 5)
        self.assertContains(detail, 'Verified purchase')
        self.assertContains(detail, 'This phone arrived in excellent condition')

    def test_comment_validation_rejects_short_review(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'rating': 3, 'comment': 'short'})
        self.assertRedirects(response, self.product.get_absolute_url())
        self.assertFalse(ProductReview.objects.exists())

    def test_review_author_uses_space_separated_full_name(self):
        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            comment='Excellent phone and fast delivery',
            status='approved',
        )
        response = self.client.get(self.product.get_absolute_url())
        self.assertContains(response, 'Real Customer')
        self.assertNotContains(response, 'Real.Customer')
        self.assertEqual(str(review), 'Real Customer - iPhone 13 (5/5)')

    def test_product_detail_renders_star_form_and_approved_star_display(self):
        self.client.force_login(self.user)
        detail_before = self.client.get(self.product.get_absolute_url())
        self.assertContains(detail_before, 'review-star-input')
        self.assertContains(detail_before, 'role="radiogroup"')
        self.assertContains(detail_before, 'aria-label="Choose a 1 to 5 star rating"')
        self.assertContains(detail_before, 'fas fa-star')

        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            comment='Excellent phone and fast delivery',
            status='approved',
        )
        detail = self.client.get(self.product.get_absolute_url())
        self.assertContains(detail, 'aria-label="4 out of 5 stars"')


class OrderScreenTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='order-viewer', password='test-password')
        self.client.force_login(user)
        model = iPhoneModel.objects.create(
            name='iPhone 16',
            release_year=2024,
            display_size='6.1 inches',
            storage_options='128GB',
        )
        color = Color.objects.create(name='Teal', hex_code='#4D9A91')
        product = iPhoneProduct.objects.create(
            iphone_model=model,
            color=color,
            storage='128GB',
            condition='new',
            grade=None,
            price=Decimal('16249.00'),
            stock_quantity=2,
        )
        self.order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('32498.00'),
            subtotal_amount=Decimal('32498.00'),
            email='buyer@example.com',
            shipping_address='15 Demo Street\nSandton, Gauteng 2196',
            billing_address='15 Demo Street\nSandton, Gauteng 2196',
            phone='010 555 0123',
        )
        OrderItem.objects.create(
            order=self.order,
            product=product,
            quantity=2,
            price=product.price,
        )

    def test_my_orders_page_uses_mobile_order_card_structure(self):
        response = self.client.get(reverse('store:order_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'order-list-card')
        self.assertContains(response, f'Order #{self.order.order_number}')
        self.assertContains(response, 'order-list-actions')
        self.assertContains(response, 'View Details')

    def test_order_detail_has_mobile_status_and_item_layout(self):
        response = self.client.get(self.order.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'order-detail-page')
        self.assertContains(response, 'progress-timeline')
        self.assertContains(response, 'order-item-row')
        self.assertContains(response, 'Shipping Information')
        self.assertContains(response, 'Order Summary')
