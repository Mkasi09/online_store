from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import quote

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from store.models import Color, iPhoneModel, iPhoneProduct, OrderItem


class Command(BaseCommand):
    help = 'Replace the product catalog with the specified iPhone inventory'

    GRADES = ('A', 'B', 'C')
    INVENTORY_COUNTS = {'used': 450, 'new': 100}
    STOCK_LEVELS = (0, 2, 5, 10)
    ESTIMATED_PRO_MODELS = {
        f'iPhone {generation} Pro{suffix}'
        for generation in range(13, 18)
        for suffix in ('', ' Max')
    }
    NEW_MODELS = {
        'iPhone 13', 'iPhone 13 Pro', 'iPhone 13 Pro Max',
        'iPhone 14', 'iPhone 14 Pro', 'iPhone 14 Pro Max',
        'iPhone 15', 'iPhone 15 Pro', 'iPhone 15 Pro Max',
        'iPhone 16', 'iPhone 16 Pro', 'iPhone 16 Pro Max',
        'iPhone 17', 'iPhone 17 Pro', 'iPhone 17 Pro Max',
        'iPhone 18 Pro', 'iPhone 18 Pro Max',
    }

    COLORS = {
        'Jet Black': '#111111',
        'Black': '#1B1B1B',
        'Silver': '#C6C8CC',
        'Gold': '#D6B66A',
        'Rose Gold': '#D5A49A',
        'Red': '#C8102E',
        'Space Grey': '#55565A',
        'White': '#F4F4F0',
        'Blue': '#4C87C8',
        'Yellow': '#F3D34A',
        'Coral': '#FF7664',
        'Green': '#73A78A',
        'Purple': '#A694C3',
        'Midnight': '#222838',
        'Starlight': '#F2EDE3',
        'Pink': '#EFAEBB',
        'Ultramarine': '#5363D9',
        'Teal': '#4D9A91',
        'Mist Blue': '#A6C5D5',
        'Sage': '#A5AF97',
        'Lavender': '#B6A9D2',
        'Graphite': '#626262',
        'Sierra Blue': '#A3BDD3',
        'Alpine Green': '#445C50',
        'Deep Purple': '#51415F',
        'Space Black': '#222222',
        'Blue Titanium': '#405368',
        'Cosmic Orange': '#FF6D24',
        'Deep Blue': '#263A6C',
        'Black Titanium': '#343438',
        'Natural Titanium': '#8F8A82',
        'White Titanium': '#E3E1DC',
        'Desert Titanium': '#B99C7C',
    }

    CATALOG = {
        'iPhone 7': {
            'year': 2016, 'display': '4.7 inches',
            'storage': ('32GB', '128GB', '256GB'),
            'colors': ('Jet Black', 'Black', 'Silver', 'Gold', 'Rose Gold', 'Red'),
            'prices': {
                '32GB': (1799, 1499, 1199), '128GB': (2099, 1799, 1499),
                '256GB': (2399, 2099, 1799),
            },
        },
        'iPhone 8': {
            'year': 2017, 'display': '4.7 inches',
            'storage': ('64GB', '128GB', '256GB'),
            'colors': ('Silver', 'Space Grey', 'Gold', 'Red'),
            'prices': {
                '64GB': (2199, 1899, 1599), '128GB': (2499, 2199, 1899),
                '256GB': (2799, 2499, 2199),
            },
        },
        'iPhone X': {
            'year': 2017, 'display': '5.8 inches',
            'storage': ('64GB', '256GB'),
            'colors': ('Silver', 'Space Grey'),
            'prices': {'64GB': (3499, 3099, 2699), '256GB': (4299, 3899, 3499)},
        },
        'iPhone XR': {
            'year': 2018, 'display': '6.1 inches',
            'storage': ('64GB', '128GB', '256GB'),
            'colors': ('Black', 'White', 'Blue', 'Yellow', 'Coral', 'Red'),
            'prices': {
                '64GB': (3899, 3499, 2999), '128GB': (4199, 3799, 3299),
                '256GB': (4599, 4199, 3699),
            },
        },
        'iPhone 11': {
            'year': 2019, 'display': '6.1 inches',
            'storage': ('64GB', '128GB', '256GB'),
            'colors': ('Black', 'White', 'Green', 'Yellow', 'Purple', 'Red'),
            'prices': {
                '64GB': (3999, 3599, 3199), '128GB': (4499, 4099, 3699),
                '256GB': (5099, 4699, 4299),
            },
        },
        'iPhone 12': {
            'year': 2020, 'display': '6.1 inches',
            'storage': ('64GB', '128GB', '256GB'),
            'colors': ('Black', 'White', 'Blue', 'Green', 'Purple', 'Red'),
            'prices': {
                '64GB': (4999, 4499, 3999), '128GB': (5399, 4899, 4399),
                '256GB': (5899, 5399, 4899),
            },
        },
        'iPhone 13': {
            'year': 2021, 'display': '6.1 inches',
            'storage': ('128GB', '256GB', '512GB'),
            'colors': ('Midnight', 'Starlight', 'Blue', 'Pink', 'Green', 'Red'),
            'prices': {
                '128GB': (6499, 5999, 5499), '256GB': (7199, 6699, 6199),
                '512GB': (7999, 7499, 6999),
            },
        },
        # Estimated Grade A/B/C baselines for newly requested Pro variants.
        'iPhone 13 Pro': {
            'year': 2021, 'display': '6.1 inches',
            'storage': ('128GB', '256GB', '512GB', '1TB'),
            'colors': ('Graphite', 'Gold', 'Silver', 'Sierra Blue', 'Alpine Green'),
            'prices': {
                '128GB': (7499, 6999, 6499), '256GB': (8199, 7699, 7199),
                '512GB': (8999, 8499, 7999), '1TB': (9799, 9299, 8799),
            },
        },
        'iPhone 13 Pro Max': {
            'year': 2021, 'display': '6.7 inches',
            'storage': ('128GB', '256GB', '512GB', '1TB'),
            'colors': ('Graphite', 'Gold', 'Silver', 'Sierra Blue', 'Alpine Green'),
            'prices': {
                '128GB': (8499, 7999, 7499), '256GB': (9199, 8699, 8199),
                '512GB': (9999, 9499, 8999), '1TB': (10799, 10299, 9799),
            },
        },
        'iPhone 14': {
            'year': 2022, 'display': '6.1 inches',
            'storage': ('128GB', '256GB', '512GB'),
            'colors': ('Midnight', 'Starlight', 'Blue', 'Purple', 'Yellow', 'Red'),
            'prices': {
                '128GB': (8499, 7999, 7499), '256GB': (9199, 8699, 8199),
                '512GB': (9999, 9499, 8999),
            },
        },
        'iPhone 14 Pro': {
            'year': 2022, 'display': '6.1 inches',
            'storage': ('128GB', '256GB', '512GB', '1TB'),
            'colors': ('Deep Purple', 'Gold', 'Silver', 'Space Black'),
            'prices': {
                '128GB': (9499, 8999, 8499), '256GB': (10199, 9699, 9199),
                '512GB': (10999, 10499, 9999), '1TB': (11799, 11299, 10799),
            },
        },
        'iPhone 14 Pro Max': {
            'year': 2022, 'display': '6.7 inches',
            'storage': ('128GB', '256GB', '512GB', '1TB'),
            'colors': ('Deep Purple', 'Gold', 'Silver', 'Space Black'),
            'prices': {
                '128GB': (10499, 9999, 9499), '256GB': (11199, 10699, 10199),
                '512GB': (11999, 11499, 10999), '1TB': (12799, 12299, 11799),
            },
        },
        'iPhone 15': {
            'year': 2023, 'display': '6.1 inches',
            'storage': ('128GB', '256GB', '512GB'),
            'colors': ('Black', 'Blue', 'Green', 'Yellow', 'Pink'),
            'prices': {
                '128GB': (9999, 9499, 8999), '256GB': (10699, 10199, 9699),
                '512GB': (11499, 10999, 10499),
            },
        },
        'iPhone 15 Pro': {
            'year': 2023, 'display': '6.1 inches',
            'storage': ('128GB', '256GB', '512GB', '1TB'),
            'colors': ('Blue Titanium', 'Natural Titanium', 'White Titanium', 'Black Titanium'),
            'prices': {
                '128GB': (11499, 10999, 10499), '256GB': (12199, 11699, 11199),
                '512GB': (12999, 12499, 11999), '1TB': (13799, 13299, 12799),
            },
        },
        'iPhone 15 Pro Max': {
            'year': 2023, 'display': '6.7 inches',
            'storage': ('256GB', '512GB', '1TB'),
            'colors': ('Blue Titanium', 'Natural Titanium', 'White Titanium', 'Black Titanium'),
            'prices': {
                '256GB': (12499, 11999, 11499), '512GB': (13299, 12799, 12299),
                '1TB': (14099, 13599, 13099),
            },
        },
        'iPhone 16': {
            'year': 2024, 'display': '6.1 inches',
            'storage': ('128GB', '256GB', '512GB'),
            'colors': ('Ultramarine', 'Teal', 'Pink', 'White', 'Black'),
            'prices': {
                '128GB': (12499, 11999, 11499), '256GB': (13199, 12699, 12199),
                '512GB': (13999, 13499, 12999),
            },
        },
        'iPhone 16 Pro': {
            'year': 2024, 'display': '6.3 inches',
            'storage': ('128GB', '256GB', '512GB', '1TB'),
            'colors': ('Desert Titanium', 'Natural Titanium', 'White Titanium', 'Black Titanium'),
            'prices': {
                '128GB': (13999, 13499, 12999), '256GB': (14699, 14199, 13699),
                '512GB': (15499, 14999, 14499), '1TB': (16299, 15799, 15299),
            },
        },
        'iPhone 16 Pro Max': {
            'year': 2024, 'display': '6.9 inches',
            'storage': ('256GB', '512GB', '1TB'),
            'colors': ('Desert Titanium', 'Natural Titanium', 'White Titanium', 'Black Titanium'),
            'prices': {
                '256GB': (15699, 15199, 14699), '512GB': (16499, 15999, 15499),
                '1TB': (17299, 16799, 16299),
            },
        },
        'iPhone 17': {
            'year': 2025, 'display': '6.3 inches',
            'storage': ('256GB', '512GB'),
            'colors': ('Black', 'White', 'Mist Blue', 'Sage', 'Lavender'),
            'prices': {'256GB': (18999, 18499, 17999), '512GB': (21499, 20999, 20499)},
        },
        'iPhone 17 Pro': {
            'year': 2025, 'display': '6.3 inches',
            'storage': ('256GB', '512GB', '1TB'),
            'colors': ('Cosmic Orange', 'Deep Blue', 'Silver'),
            'prices': {
                '256GB': (19999, 19499, 18999), '512GB': (22499, 21999, 21499),
                '1TB': (24999, 24499, 23999),
            },
        },
        'iPhone 17 Pro Max': {
            'year': 2025, 'display': '6.9 inches',
            'storage': ('256GB', '512GB', '1TB'),
            'colors': ('Cosmic Orange', 'Deep Blue', 'Silver'),
            'prices': {
                '256GB': (21999, 21499, 20999), '512GB': (24499, 23999, 23499),
                '1TB': (26999, 26499, 25999),
            },
        },
        'iPhone 18 Pro': {
            'year': None, 'display': '',
            'storage': ('256GB', '512GB', '1TB'),
            'colors': ('Black Titanium', 'Natural Titanium', 'White Titanium', 'Desert Titanium'),
            'prices': {
                '256GB': (30499, 29999, 29499), '512GB': (33499, 32999, 32499),
                '1TB': (36499, 35999, 35499),
            },
        },
        'iPhone 18 Pro Max': {
            'year': None, 'display': '',
            'storage': ('256GB', '512GB'),
            'colors': ('Black Titanium', 'Natural Titanium', 'White Titanium', 'Desert Titanium'),
            'prices': {
                '256GB': (33499, 32999, 32499), '512GB': (36499, 35999, 35499),
            },
        },
    }

    IMAGE_DEVICE_KEYS = {
        'iPhone 7': 'iPhone9,1',
        'iPhone 8': 'iPhone10,1',
        'iPhone X': 'iPhone10,3',
        'iPhone XR': 'iPhone11,8',
        'iPhone 11': 'iPhone12,1',
        'iPhone 12': 'iPhone13,2',
        'iPhone 13': 'iPhone14,5',
        'iPhone 14': 'iPhone14,7',
        'iPhone 15': 'iPhone15,4',
        'iPhone 16': 'iPhone17,3',
        'iPhone 17': 'iPhone18,3',
        'iPhone 13 Pro': 'iPhone14,2',
        'iPhone 13 Pro Max': 'iPhone14,3',
        'iPhone 14 Pro': 'iPhone15,2',
        'iPhone 14 Pro Max': 'iPhone15,3',
        'iPhone 15 Pro': 'iPhone16,1',
        'iPhone 15 Pro Max': 'iPhone16,2',
        'iPhone 16 Pro': 'iPhone17,1',
        'iPhone 16 Pro Max': 'iPhone17,2',
        'iPhone 17 Pro': 'iPhone18,1',
        'iPhone 17 Pro Max': 'iPhone18,2',
    }

    LOCAL_IMAGE_FILES = {
        'iPhone 18 Pro': {
            'Black Titanium': 'iphone_images/iphone_18_black.png',
            'Desert Titanium': 'iphone_images/iphone_18_desert.png',
            'Natural Titanium': 'iphone_images/iphone_18_natural.png',
            'White Titanium': 'iphone_images/iphone_18_white.png',
        },
        'iPhone 18 Pro Max': {
            'Black Titanium': 'iphone_images/iphone_18_black.png',
            'Desert Titanium': 'iphone_images/iphone_18_desert.png',
            'Natural Titanium': 'iphone_images/iphone_18_natural.png',
            'White Titanium': 'iphone_images/iphone_18_white.png',
        },
    }

    IMAGE_COLOR_KEYS = {
        'iPhone 7': {
            'Jet Black': 'Jet Black', 'Black': 'Black', 'Silver': 'Silver',
            'Gold': 'Gold', 'Rose Gold': 'Rose Gold', 'Red': '(PRODUCT)RED',
        },
        'iPhone 8': {
            'Silver': 'Silver', 'Space Grey': 'Space Gray', 'Gold': 'Gold',
            'Red': '(PRODUCT)RED',
        },
        'iPhone X': {'Silver': 'Silver', 'Space Grey': 'Space Gray'},
        'iPhone XR': {
            'Black': 'Black', 'White': 'White', 'Blue': 'Blue',
            'Yellow': 'Yellow', 'Coral': 'Coral', 'Red': '(PRODUCT)RED',
        },
        'iPhone 11': {
            'Black': 'Black', 'White': 'White', 'Green': 'Green',
            'Yellow': 'Yellow', 'Purple': 'Purple', 'Red': '(PRODUCT)RED',
        },
        'iPhone 12': {
            'Black': 'Black', 'White': 'White', 'Blue': 'Blue',
            'Green': 'Green', 'Purple': 'Purple', 'Red': '(PRODUCT)RED',
        },
        'iPhone 13': {
            'Midnight': 'Midnight', 'Starlight': 'Starlight', 'Blue': 'Blue',
            'Pink': 'Pink', 'Green': 'Green', 'Red': '(PRODUCT)RED',
        },
        'iPhone 14': {
            'Midnight': 'Midnight', 'Starlight': 'Starlight', 'Blue': 'Blue',
            'Purple': 'Purple', 'Yellow': 'Yellow', 'Red': '(PRODUCT)RED',
        },
        'iPhone 15': {
            'Black': 'Black', 'Blue': 'Blue', 'Green': 'Green',
            'Yellow': 'Yellow', 'Pink': 'Pink',
        },
        'iPhone 16': {
            'Ultramarine': 'Ultramarine', 'Teal': 'Teal', 'Pink': 'Pink',
            'White': 'White', 'Black': 'Black',
        },
        'iPhone 17': {
            'Black': 'Black', 'White': 'White', 'Mist Blue': 'Mist Blue',
            'Sage': 'Sage', 'Lavender': 'Lavender',
        },
        'iPhone 13 Pro': {
            'Graphite': 'Graphite', 'Gold': 'Gold', 'Silver': 'Silver',
            'Sierra Blue': 'Sierra Blue', 'Alpine Green': 'Alpine Green',
        },
        'iPhone 13 Pro Max': {
            'Graphite': 'Graphite', 'Gold': 'Gold', 'Silver': 'Silver',
            'Sierra Blue': 'Sierra Blue', 'Alpine Green': 'Alpine Green',
        },
        'iPhone 14 Pro': {
            'Deep Purple': 'Deep Purple', 'Gold': 'Gold', 'Silver': 'Silver',
            'Space Black': 'Space Black',
        },
        'iPhone 14 Pro Max': {
            'Deep Purple': 'Deep Purple', 'Gold': 'Gold', 'Silver': 'Silver',
            'Space Black': 'Space Black',
        },
        'iPhone 15 Pro': {
            'Blue Titanium': 'Blue Titanium', 'Natural Titanium': 'Natural Titanium',
            'White Titanium': 'White Titanium', 'Black Titanium': 'Black Titanium',
        },
        'iPhone 15 Pro Max': {
            'Blue Titanium': 'Blue Titanium', 'Natural Titanium': 'Natural Titanium',
            'White Titanium': 'White Titanium', 'Black Titanium': 'Black Titanium',
        },
        'iPhone 16 Pro': {
            'Desert Titanium': 'Desert Titanium', 'Natural Titanium': 'Natural Titanium',
            'White Titanium': 'White Titanium', 'Black Titanium': 'Black Titanium',
        },
        'iPhone 16 Pro Max': {
            'Desert Titanium': 'Desert Titanium', 'Natural Titanium': 'Natural Titanium',
            'White Titanium': 'White Titanium', 'Black Titanium': 'Black Titanium',
        },
        'iPhone 17 Pro': {
            'Cosmic Orange': 'Cosmic Orange', 'Deep Blue': 'Deep Blue', 'Silver': 'Silver',
        },
        'iPhone 17 Pro Max': {
            'Cosmic Orange': 'Cosmic Orange', 'Deep Blue': 'Deep Blue', 'Silver': 'Silver',
        },
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm-reset',
            action='store_true',
            help='Required: delete the existing catalog before adding this inventory.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show the catalog size without changing the database.',
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Update prices and add verified catalog variants without deleting existing data.',
        )

    def handle(self, *args, **options):
        if options['sync']:
            if options['dry_run']:
                self.stdout.write(
                    f'Would sync prices and add variants for {len(self.CATALOG)} iPhone models.'
                )
                return
            with transaction.atomic():
                self.sync_catalog()
            return

        product_count = sum(self.INVENTORY_COUNTS.values())
        if options['dry_run']:
            inventory = ', '.join(
                f'{count} {condition}' for condition, count in self.INVENTORY_COUNTS.items()
            )
            self.stdout.write(
                f'Would replace the catalog with {len(self.CATALOG)} models and {product_count} products '
                f'({inventory}).'
            )
            return
        if not options['confirm_reset']:
            raise CommandError('This replaces the entire product catalog. Rerun with --confirm-reset to proceed.')

        with transaction.atomic():
            old_products = iPhoneProduct.objects.count()
            old_models = iPhoneModel.objects.count()
            old_colors = Color.objects.count()

            iPhoneProduct.objects.all().delete()
            iPhoneModel.objects.all().delete()
            Color.objects.all().delete()

            self.create_colors()
            self.create_models()
            self.create_products()

        self.stdout.write(self.style.SUCCESS(
            f'Replaced {old_products} products, {old_models} models, and {old_colors} colors '
            f'with {product_count} products across {len(self.CATALOG)} iPhone models.'
        ))

    def sync_catalog(self):
        if iPhoneProduct.objects.filter(
            is_active=True,
            condition='refurbished',
        ).exists():
            raise CommandError('Run the catalog migration before syncing the new model variants.')

        created_models = 0
        created_colors = 0
        updated_products = 0

        model_lookup = {}
        for name, data in self.CATALOG.items():
            description = (
                f'{name} catalog inventory with the storage options listed below.'
                if name.startswith('iPhone 18')
                else f'{name} inventory with {data["display"]} display and the storage options listed below.'
            )
            model, created = iPhoneModel.objects.get_or_create(
                name=name,
                defaults={
                    'release_year': data['year'],
                    'display_size': data['display'],
                    'storage_options': ', '.join(data['storage']),
                    'description': description,
                },
            )
            if created:
                created_models += 1
            elif model.storage_options != ', '.join(data['storage']):
                model.storage_options = ', '.join(data['storage'])
                model.save(update_fields=['storage_options'])
            model_lookup[name] = model

        color_lookup = {}
        for name, hex_code in self.COLORS.items():
            if not any(name in data['colors'] for data in self.CATALOG.values()):
                continue
            color, created = Color.objects.get_or_create(
                name=name,
                defaults={'hex_code': hex_code},
            )
            created_colors += int(created)
            color_lookup[name] = color

        for product in iPhoneProduct.objects.select_related('iphone_model').all():
            data = self.CATALOG.get(product.iphone_model.name)
            if data is None or product.storage not in data['prices']:
                if product.iphone_model.name == 'iPhone 18 Pro Max':
                    product.is_active = False
                    product.save(update_fields=['is_active'])
                continue

            if product.condition == 'new':
                if product.iphone_model.name not in self.NEW_MODELS:
                    product.is_active = False
                    product.save(update_fields=['is_active'])
                    continue
                price = self.discount_price(
                    self.new_price_from_grade_a(data['prices'][product.storage][0])
                )
            else:
                grade = product.grade or 'A'
                if grade not in self.GRADES:
                    continue
                price = self.discount_price(
                    data['prices'][product.storage][self.GRADES.index(grade)]
                )
            if product.price != price:
                product.price = price
                product.save(update_fields=['price'])
                updated_products += 1

        products_to_create = []
        stock_index = 0
        for model_name in sorted(self.ESTIMATED_PRO_MODELS):
            data = self.CATALOG[model_name]
            model = model_lookup[model_name]
            for color_name in data['colors']:
                color = color_lookup[color_name]
                image_url = self.get_product_image(model_name, color_name)
                for storage in data['storage']:
                    for grade in self.GRADES:
                        key = (model.pk, color.pk, storage, 'used', grade)
                        if iPhoneProduct.objects.filter(
                            iphone_model_id=key[0],
                            color_id=key[1],
                            storage=key[2],
                            condition=key[3],
                            grade=key[4],
                        ).exists():
                            continue
                        products_to_create.append(iPhoneProduct(
                            iphone_model=model,
                            color=color,
                            storage=storage,
                            condition='used',
                            grade=grade,
                            price=self.discount_price(
                                data['prices'][storage][self.GRADES.index(grade)]
                            ),
                            stock_quantity=self.STOCK_LEVELS[stock_index % len(self.STOCK_LEVELS)],
                            image_url=image_url,
                            image=self.get_product_local_image(model_name, color_name),
                            is_active=True,
                        ))
                        stock_index += 1

                    key = (model.pk, color.pk, storage, 'new', None)
                    if not iPhoneProduct.objects.filter(
                        iphone_model_id=key[0],
                        color_id=key[1],
                        storage=key[2],
                        condition=key[3],
                        grade=key[4],
                    ).exists():
                        products_to_create.append(iPhoneProduct(
                            iphone_model=model,
                            color=color,
                            storage=storage,
                            condition='new',
                            grade=None,
                            price=self.discount_price(
                                self.new_price_from_grade_a(data['prices'][storage][0])
                            ),
                            stock_quantity=self.STOCK_LEVELS[stock_index % len(self.STOCK_LEVELS)],
                            image_url=image_url,
                            image=self.get_product_local_image(model_name, color_name),
                            is_active=True,
                        ))
                        stock_index += 1

        iPhoneProduct.objects.bulk_create(products_to_create, batch_size=500)
        self.stdout.write(self.style.SUCCESS(
            f'Synced catalog prices for {updated_products} products; added '
            f'{created_models} models, {created_colors} colors, and '
            f'{len(products_to_create)} Pro model variants without deleting existing data.'
        ))

    def create_colors(self):
        Color.objects.bulk_create([
            Color(name=name, hex_code=hex_code)
            for name, hex_code in self.COLORS.items()
            if any(name in data['colors'] for data in self.CATALOG.values())
        ])

    def create_models(self):
        models = []
        for name, data in self.CATALOG.items():
            if name.startswith('iPhone 18'):
                description = f'{name} catalog inventory with the storage options listed below.'
            else:
                description = (
                    f'{name} inventory with {data["display"]} display and the storage options listed below.'
                )
            models.append(iPhoneModel(
                name=name,
                release_year=data['year'],
                display_size=data['display'],
                storage_options=', '.join(data['storage']),
                description=description,
            ))
        iPhoneModel.objects.bulk_create(models)

    def create_products(self):
        model_lookup = {model.name: model for model in iPhoneModel.objects.all()}
        color_lookup = {color.name: color for color in Color.objects.all()}
        candidates = []
        new_candidates = []
        for model_name, data in self.CATALOG.items():
            model = model_lookup[model_name]
            for color_name in data['colors']:
                image_url = self.get_product_image(model_name, color_name)
                for storage in data['storage']:
                    for grade_index, grade in enumerate(self.GRADES):
                        candidates.append((
                            model_name,
                            model,
                            color_lookup[color_name],
                            storage,
                            grade,
                            self.discount_price(data['prices'][storage][grade_index]),
                            image_url,
                        ))
                    if model_name in self.NEW_MODELS:
                        new_candidates.append((
                            model_name,
                            model,
                            color_lookup[color_name],
                            storage,
                            None,
                            self.discount_price(
                                self.new_price_from_grade_a(data['prices'][storage][0])
                            ),
                            image_url,
                        ))

        products = []
        candidate_groups = {
            'used': candidates,
            'new': new_candidates,
        }
        for condition_index, (condition, count) in enumerate(self.INVENTORY_COUNTS.items()):
            eligible = candidate_groups[condition]
            for product_index in range(count):
                candidate_index = (product_index * len(eligible)) // count
                _, model, color, storage, grade, price, image_url = eligible[candidate_index]
                products.append(iPhoneProduct(
                    iphone_model=model,
                    color=color,
                    storage=storage,
                    condition=condition,
                    grade=grade,
                    price=price,
                    stock_quantity=self.STOCK_LEVELS[
                        (product_index + condition_index) % len(self.STOCK_LEVELS)
                    ],
                    image_url=image_url,
                    image=self.get_product_local_image(model.name, color.name),
                    is_active=True,
                ))
        iPhoneProduct.objects.bulk_create(products, batch_size=500)

    @staticmethod
    def new_price_from_grade_a(grade_a_price):
        return int(
            (Decimal(grade_a_price) * Decimal('1.30')).quantize(
                Decimal('1'),
                rounding=ROUND_HALF_UP,
            )
        )

    @staticmethod
    def discount_price(price):
        discounted = (
            Decimal(price) * Decimal('0.80')
        ).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return Command.round_to_nearest_hundred(discounted)

    @staticmethod
    def round_to_nearest_hundred(price):
        return int(
            (Decimal(price) / Decimal('100')).quantize(
                Decimal('1'),
                rounding=ROUND_HALF_UP,
            ) * Decimal('100')
        )

    def get_product_image(self, model_name, color_name):
        if model_name in self.LOCAL_IMAGE_FILES:
            return ''
        device_key = self.IMAGE_DEVICE_KEYS.get(model_name)
        color_key = self.IMAGE_COLOR_KEYS.get(model_name, {}).get(color_name)
        if not device_key or not color_key:
            return ''
        encoded_device_key = quote(device_key, safe=',')
        encoded_color_key = quote(color_key, safe='')
        return f'https://img.appledb.dev/device@256/{encoded_device_key}/{encoded_color_key}.png'

    def get_product_local_image(self, model_name, color_name):
        return self.LOCAL_IMAGE_FILES.get(model_name, {}).get(color_name, '')
