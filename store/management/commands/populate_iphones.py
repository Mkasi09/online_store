from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import Color, iPhoneModel, iPhoneProduct

import random


class Command(BaseCommand):
    help = 'Populate the database with verified real iPhone product images'

    CONDITIONS = ('new', 'refurbished', 'used')

    COLORS = {
        'Black': '#000000',
        'White': '#FFFFFF',
        'Silver': '#C0C0C0',
        'Space Gray': '#4A4A4A',
        'Gold': '#FFD700',
        'Red': '#FF0000',
        'Blue': '#0000FF',
        'Purple': '#800080',
        'Yellow': '#FFFF00',
        'Orange': '#FF9500',
        'Pacific Blue': '#0077BE',
        'Graphite': '#36454F',
        'Sierra Blue': '#4A90E2',
        'Deep Purple': '#301934',
        'Starlight': '#F8E7D2',
        'Midnight': '#1C1C1C',
        'Pink': '#FFC0CB',
        'Green': '#008000',
        'Space Black': '#1F1F1F',
        'Teal': '#3F8F8C',
        'Ultramarine': '#5F6FEA',
    }

    CATALOG = {
        'iPhone X': {
            'year': 2017,
            'display': '5.8 inches',
            'storage': ('64GB', '256GB'),
            'colors': ('Space Gray',),
        },
        'iPhone XR': {
            'year': 2018,
            'display': '6.1 inches',
            'storage': ('64GB', '128GB', '256GB'),
            'colors': ('Black', 'White'),
        },
        'iPhone XS Max': {
            'year': 2018,
            'display': '6.5 inches',
            'storage': ('64GB', '256GB', '512GB'),
            'colors': ('Gold',),
        },
        'iPhone 11': {
            'year': 2019,
            'display': '6.1 inches',
            'storage': ('64GB', '128GB', '256GB'),
            'colors': ('Purple', 'Green', 'Red'),
        },
        'iPhone 11 Pro': {
            'year': 2019,
            'display': '5.8 inches',
            'storage': ('64GB', '256GB', '512GB'),
            'colors': ('Space Gray',),
        },
        'iPhone 11 Pro Max': {
            'year': 2019,
            'display': '6.5 inches',
            'storage': ('64GB', '256GB', '512GB'),
            'colors': ('Gold',),
        },
        'iPhone 12 Pro': {
            'year': 2020,
            'display': '6.1 inches',
            'storage': ('128GB', '256GB', '512GB'),
            'colors': ('Graphite', 'Silver', 'Gold', 'Pacific Blue'),
        },
        'iPhone 12 Pro Max': {
            'year': 2020,
            'display': '6.7 inches',
            'storage': ('128GB', '256GB', '512GB'),
            'colors': ('Graphite', 'Silver', 'Gold', 'Pacific Blue'),
        },
        'iPhone 13 mini': {
            'year': 2021,
            'display': '5.4 inches',
            'storage': ('128GB', '256GB', '512GB'),
            'colors': ('Starlight', 'Blue', 'Pink', 'Green'),
        },
        'iPhone 13': {
            'year': 2021,
            'display': '6.1 inches',
            'storage': ('128GB', '256GB', '512GB'),
            'colors': ('Starlight', 'Blue', 'Pink', 'Green'),
        },
        'iPhone 13 Pro': {
            'year': 2021,
            'display': '6.1 inches',
            'storage': ('128GB', '256GB', '512GB', '1TB'),
            'colors': ('Graphite', 'Silver', 'Sierra Blue'),
        },
        'iPhone 13 Pro Max': {
            'year': 2021,
            'display': '6.7 inches',
            'storage': ('128GB', '256GB', '512GB', '1TB'),
            'colors': ('Graphite', 'Silver', 'Sierra Blue'),
        },
        'iPhone 14': {
            'year': 2022,
            'display': '6.1 inches',
            'storage': ('128GB', '256GB', '512GB'),
            'colors': ('Midnight', 'Starlight', 'Blue', 'Yellow'),
        },
        'iPhone 14 Plus': {
            'year': 2022,
            'display': '6.7 inches',
            'storage': ('128GB', '256GB', '512GB'),
            'colors': ('Midnight', 'Starlight', 'Blue', 'Yellow'),
        },
        'iPhone 14 Pro': {
            'year': 2022,
            'display': '6.1 inches',
            'storage': ('128GB', '256GB', '512GB', '1TB'),
            'colors': ('Space Black', 'Silver', 'Gold', 'Deep Purple'),
        },
        'iPhone 14 Pro Max': {
            'year': 2022,
            'display': '6.7 inches',
            'storage': ('128GB', '256GB', '512GB', '1TB'),
            'colors': ('Space Black', 'Silver', 'Gold', 'Deep Purple'),
        },
        'iPhone 16': {
            'year': 2024,
            'display': '6.1 inches',
            'storage': ('128GB', '256GB', '512GB', '1TB'),
            'colors': ('Black', 'White', 'Pink', 'Teal', 'Ultramarine'),
        },
        'iPhone 16 Plus': {
            'year': 2024,
            'display': '6.7 inches',
            'storage': ('128GB', '256GB', '512GB', '1TB'),
            'colors': ('Black', 'White', 'Pink', 'Teal', 'Ultramarine'),
        },
        'iPhone 17': {
            'year': 2025,
            'display': '6.3 inches',
            'storage': ('256GB', '512GB', '1TB'),
            'colors': ('Black',),
        },
        'iPhone 17 Pro': {
            'year': 2025,
            'display': '6.3 inches',
            'storage': ('256GB', '512GB', '1TB', '2TB'),
            'colors': ('Orange', 'Silver'),
        },
        'iPhone 17 Pro Max': {
            'year': 2025,
            'display': '6.9 inches',
            'storage': ('256GB', '512GB', '1TB', '2TB'),
            'colors': ('Orange', 'Silver'),
        },
    }

    IMAGE_MAP = {
        ('iPhone X', 'Space Gray'): 'iphone_images/iphone_x_pngall_main.png',
        ('iPhone XR', 'Black'): 'iphone_images/iphone_xr_pngall_5.png',
        ('iPhone XR', 'White'): 'iphone_images/iphone_xr_pngall_4.png',
        ('iPhone XS Max', 'Gold'): 'iphone_images/iphone_xs_max_applewiki_gold.jpg',
        ('iPhone 11', 'Purple'): 'iphone_images/iphone_11_pngall_purple.png',
        ('iPhone 11', 'Green'): 'iphone_images/iphone_11_pngall_green.png',
        ('iPhone 11', 'Red'): 'iphone_images/iphone_11_pngall_red.png',
        ('iPhone 11 Pro', 'Space Gray'): 'iphone_images/iphone_11_pro_pngall_1.png',
        ('iPhone 11 Pro Max', 'Gold'): 'iphone_images/iphone_11_pro_max_applewiki_gold.png',
        ('iPhone 12 Pro', 'Graphite'): 'iphone_images/iphone_12_pro_graphite_pdp_image_position-2__en-us_1_1.webp',
        ('iPhone 12 Pro', 'Silver'): 'iphone_images/iphone_12_pro_silver_pdp_image_position-2__en-us_1_2.webp',
        ('iPhone 12 Pro', 'Gold'): 'iphone_images/iphone_12_pro_gold_pdp_image_position-2__en-us_1_2.webp',
        ('iPhone 12 Pro', 'Pacific Blue'): 'iphone_images/iphone_12_pro_pacific_blue_pdp_image_position-2__en-us_1_3.webp',
        ('iPhone 12 Pro Max', 'Graphite'): 'iphone_images/iphone_12_pro_graphite_pdp_image_position-2__en-us_1_1.webp',
        ('iPhone 12 Pro Max', 'Silver'): 'iphone_images/iphone_12_pro_silver_pdp_image_position-2__en-us_1_2.webp',
        ('iPhone 12 Pro Max', 'Gold'): 'iphone_images/iphone_12_pro_gold_pdp_image_position-2__en-us_1_2.webp',
        ('iPhone 12 Pro Max', 'Pacific Blue'): 'iphone_images/iphone_12_pro_pacific_blue_pdp_image_position-2__en-us_1_3.webp',
        ('iPhone 13 mini', 'Starlight'): 'iphone_images/iphone_13_starlight_pdp_image_position-1a__wwen.jpg',
        ('iPhone 13 mini', 'Blue'): 'iphone_images/iphone_13_blue_pdp_image_position-1a__wwen.jpg',
        ('iPhone 13 mini', 'Pink'): 'iphone_images/iphone_13_pink_pdp_image_position-1a__wwen.jpg',
        ('iPhone 13 mini', 'Green'): 'iphone_images/iphone_13_green_pdp_image_position-1a__wwen.jpg',
        ('iPhone 13', 'Starlight'): 'iphone_images/iphone_13_starlight_pdp_image_position-1a__wwen.jpg',
        ('iPhone 13', 'Blue'): 'iphone_images/iphone_13_blue_pdp_image_position-1a__wwen.jpg',
        ('iPhone 13', 'Pink'): 'iphone_images/iphone_13_pink_pdp_image_position-1a__wwen.jpg',
        ('iPhone 13', 'Green'): 'iphone_images/iphone_13_green_pdp_image_position-1a__wwen.jpg',
        ('iPhone 13 Pro', 'Graphite'): 'iphone_images/iphone_13_pro_graphite_pdp_image_position-1a__wwen.jpg',
        ('iPhone 13 Pro', 'Silver'): 'iphone_images/iphone_13_pro_silver_pdp_image_position-1a__wwen.jpg',
        ('iPhone 13 Pro', 'Sierra Blue'): 'iphone_images/iphone_13_pro_sierra_blue_pdp_image_position-1a__wwen.jpg',
        ('iPhone 13 Pro Max', 'Graphite'): 'iphone_images/iphone_13_pro_graphite_pdp_image_position-1a__wwen.jpg',
        ('iPhone 13 Pro Max', 'Silver'): 'iphone_images/iphone_13_pro_silver_pdp_image_position-1a__wwen.jpg',
        ('iPhone 13 Pro Max', 'Sierra Blue'): 'iphone_images/iphone_13_pro_sierra_blue_pdp_image_position-1a__wwen.jpg',
        ('iPhone 14', 'Midnight'): 'iphone_images/iphone_14_midnight-5_3_2.webp',
        ('iPhone 14', 'Starlight'): 'iphone_images/iphone_14_starlight-5_3_2.webp',
        ('iPhone 14', 'Blue'): 'iphone_images/iphone_14_blue-5_3.webp',
        ('iPhone 14', 'Yellow'): 'iphone_images/iphone_14_yellow_pdp_image_position-1a__wwen_1.webp',
        ('iPhone 14 Plus', 'Midnight'): 'iphone_images/iphone_14_midnight-5_3_2.webp',
        ('iPhone 14 Plus', 'Starlight'): 'iphone_images/iphone_14_starlight-5_3_2.webp',
        ('iPhone 14 Plus', 'Blue'): 'iphone_images/iphone_14_blue-5_3.webp',
        ('iPhone 14 Plus', 'Yellow'): 'iphone_images/iphone_14_yellow_pdp_image_position-1a__wwen_1.webp',
        ('iPhone 14 Pro', 'Space Black'): 'iphone_images/iphone_14_pro_space_black_pdp_image_position-1a__wwen.jpg',
        ('iPhone 14 Pro', 'Silver'): 'iphone_images/iphone_14_pro_silver_pdp_image_position-1a__wwen.jpg',
        ('iPhone 14 Pro', 'Gold'): 'iphone_images/iphone_14_pro_gold_pdp_image_position-1a__wwen.jpg',
        ('iPhone 14 Pro', 'Deep Purple'): 'iphone_images/iphone_14_pro_deep_purple_pdp_image_position-1a__wwen.jpg',
        ('iPhone 14 Pro Max', 'Space Black'): 'iphone_images/iphone_14_pro_space_black_pdp_image_position-1a__wwen.jpg',
        ('iPhone 14 Pro Max', 'Silver'): 'iphone_images/iphone_14_pro_silver_pdp_image_position-1a__wwen.jpg',
        ('iPhone 14 Pro Max', 'Gold'): 'iphone_images/iphone_14_pro_gold_pdp_image_position-1a__wwen.jpg',
        ('iPhone 14 Pro Max', 'Deep Purple'): 'iphone_images/iphone_14_pro_deep_purple_pdp_image_position-1a__wwen.jpg',
        ('iPhone 16', 'Black'): 'iphone_images/iphone_16_black_pdp_image_position_1__wwen.png',
        ('iPhone 16', 'White'): 'iphone_images/iphone_16_white_pdp_image_position_1__wwen.png',
        ('iPhone 16', 'Pink'): 'iphone_images/iphone_16_pink_pdp_image_position_1__wwen.png',
        ('iPhone 16', 'Teal'): 'iphone_images/iphone_16_teal_pdp_image_position_1__wwen.png',
        ('iPhone 16', 'Ultramarine'): 'iphone_images/iphone_16_ultramarine_pdp_image_position_1__wwen.png',
        ('iPhone 16 Plus', 'Black'): 'iphone_images/iphone_16_black_pdp_image_position_1__wwen.png',
        ('iPhone 16 Plus', 'White'): 'iphone_images/iphone_16_white_pdp_image_position_1__wwen.png',
        ('iPhone 16 Plus', 'Pink'): 'iphone_images/iphone_16_pink_pdp_image_position_1__wwen.png',
        ('iPhone 16 Plus', 'Teal'): 'iphone_images/iphone_16_teal_pdp_image_position_1__wwen.png',
        ('iPhone 16 Plus', 'Ultramarine'): 'iphone_images/iphone_16_ultramarine_pdp_image_position_1__wwen.png',
        ('iPhone 17', 'Black'): 'iphone_images/iphone_17_black_pdp_image_position_1__wwen_1_1.webp',
        ('iPhone 17 Pro', 'Orange'): 'iphone_images/iphone_17_pro_cosmic_orange_pdp_image_position_1__wwen_3.webp',
        ('iPhone 17 Pro', 'Silver'): 'iphone_images/iphone_17_pro_max_silver_pdp_image_position_1__wwen_3.webp',
        ('iPhone 17 Pro Max', 'Orange'): 'iphone_images/iphone_17_pro_cosmic_orange_pdp_image_position_1__wwen_3.webp',
        ('iPhone 17 Pro Max', 'Silver'): 'iphone_images/iphone_17_pro_max_silver_pdp_image_position_1__wwen_3.webp',
    }

    def handle(self, *args, **options):
        with transaction.atomic():
            self.create_colors()
            self.create_iphone_models()
            self.cleanup_catalog()
            self.create_products()
            self.stdout.write(self.style.SUCCESS('Successfully populated verified iPhone image data!'))

    def create_colors(self):
        for name, hex_code in self.COLORS.items():
            Color.objects.update_or_create(name=name, defaults={'hex_code': hex_code})

    def create_iphone_models(self):
        for name, data in self.CATALOG.items():
            iPhoneModel.objects.update_or_create(
                name=name,
                defaults={
                    'release_year': data['year'],
                    'display_size': data['display'],
                    'storage_options': ', '.join(data['storage']),
                    'description': f'The {name} features a {data["display"]} display and was released in {data["year"]}.',
                },
            )

    def cleanup_catalog(self):
        valid_models = set(self.CATALOG)
        valid_products = {
            (model_name, color_name, storage, condition)
            for model_name, data in self.CATALOG.items()
            for color_name in data['colors']
            for storage in data['storage']
            for condition in self.CONDITIONS
        }

        deleted_products = iPhoneProduct.objects.exclude(iphone_model__name__in=valid_models).count()
        iPhoneProduct.objects.exclude(iphone_model__name__in=valid_models).delete()

        for product in iPhoneProduct.objects.select_related('iphone_model', 'color'):
            key = (product.iphone_model.name, product.color.name, product.storage, product.condition)
            if key not in valid_products:
                product.delete()
                deleted_products += 1

        deleted_models = iPhoneModel.objects.exclude(name__in=valid_models).count()
        iPhoneModel.objects.exclude(name__in=valid_models).delete()

        if deleted_products or deleted_models:
            self.stdout.write(f'Removed stale products: {deleted_products}')
            self.stdout.write(f'Removed stale models: {deleted_models}')

    def create_products(self):
        created = 0
        updated = 0

        for model_name, data in self.CATALOG.items():
            model = iPhoneModel.objects.get(name=model_name)
            for color_name in data['colors']:
                color = Color.objects.get(name=color_name)
                product_image = self.get_product_image(model_name, color_name)

                for storage in data['storage']:
                    for condition in self.CONDITIONS:
                        price = self.calculate_price(data['year'], storage, condition)
                        stock = random.randint(1, 50) if condition == 'new' else random.randint(1, 20)
                        product, was_created = iPhoneProduct.objects.get_or_create(
                            iphone_model=model,
                            color=color,
                            storage=storage,
                            condition=condition,
                            defaults={
                                'price': price,
                                'stock_quantity': stock,
                                'image': product_image,
                                'cover_photo': product_image,
                                'is_active': True,
                            },
                        )

                        if was_created:
                            created += 1
                            continue

                        fields = []
                        if product.price != price:
                            product.price = price
                            fields.append('price')
                        if product.stock_quantity == 0 or not product.is_active:
                            product.stock_quantity = stock
                            product.is_active = True
                            fields.extend(['stock_quantity', 'is_active'])
                        if product.image.name != product_image or product.cover_photo.name != product_image:
                            product.image = product_image
                            product.cover_photo = product_image
                            fields.extend(['image', 'cover_photo'])

                        if fields:
                            product.save(update_fields=[*set(fields), 'updated_at'])
                            updated += 1

        self.stdout.write(f'Total products created: {created}')
        self.stdout.write(f'Total products updated: {updated}')

    def calculate_price(self, release_year, storage, condition):
        base_prices = {
            2017: 250,
            2018: 350,
            2019: 450,
            2020: 550,
            2021: 650,
            2022: 750,
            2024: 950,
            2025: 1050,
        }
        storage_multipliers = {
            '64GB': 1.0,
            '128GB': 1.2,
            '256GB': 1.4,
            '512GB': 1.8,
            '1TB': 2.2,
            '2TB': 2.8,
        }
        condition_multipliers = {
            'new': 1.0,
            'refurbished': 0.8,
            'used': 0.6,
        }
        price = base_prices[release_year] * storage_multipliers[storage] * condition_multipliers[condition]
        return round(price / 10) * 100

    def get_product_image(self, model_name, color_name):
        try:
            return self.IMAGE_MAP[(model_name, color_name)]
        except KeyError as error:
            raise ValueError(f'Missing verified phone image for {model_name} {color_name}') from error
