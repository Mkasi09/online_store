from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations


def round_to_nearest_hundred(value):
    return (
        (Decimal(value) / Decimal('100')).quantize(
            Decimal('1'),
            rounding=ROUND_HALF_UP,
        ) * Decimal('100')
    )


def round_active_catalog_prices(apps, schema_editor):
    iPhoneProduct = apps.get_model('store', 'iPhoneProduct')
    for product in iPhoneProduct.objects.filter(is_active=True).iterator():
        rounded = round_to_nearest_hundred(product.price)
        if product.price != rounded:
            product.price = rounded
            product.save(update_fields=['price'])


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0028_add_pro_colors'),
    ]

    operations = [
        migrations.RunPython(round_active_catalog_prices, migrations.RunPython.noop),
    ]
