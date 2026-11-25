from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations


def discount_and_scope_products(apps, schema_editor):
    Product = apps.get_model('store', 'iPhoneProduct')
    CartItem = apps.get_model('store', 'CartItem')
    using = schema_editor.connection.alias

    products = list(Product.objects.using(using).select_related(
        'iphone_model',
    ).order_by('pk'))
    for product in products:
        product.price = (
            (Decimal(product.price) * Decimal('0.80')).quantize(
                Decimal('1'),
                rounding=ROUND_HALF_UP,
            )
        )
        product.save(using=using, update_fields=['price'])

    for product in products:
        name = product.iphone_model.name
        if name == 'iPhone 18 Pro Max' and product.storage in {'1TB', '2TB'}:
            Product.objects.using(using).filter(pk=product.pk).update(is_active=False)
            continue

        model_number = int(name.split()[1]) if name.split()[1].isdigit() else None
        if product.condition != 'refurbished' and not (
            product.condition == 'new' and model_number is not None and model_number <= 12
        ):
            continue

        target_grade = product.grade or 'A'
        target = Product.objects.using(using).filter(
            iphone_model_id=product.iphone_model_id,
            color_id=product.color_id,
            storage=product.storage,
            condition='used',
            grade=target_grade,
        ).exclude(pk=product.pk).first()

        if target is None:
            Product.objects.using(using).filter(pk=product.pk).update(
                condition='used',
                grade=target_grade,
            )
            continue

        target.stock_quantity += product.stock_quantity
        target.is_active = target.is_active or product.is_active
        target.save(using=using, update_fields=['stock_quantity', 'is_active'])

        for item in CartItem.objects.using(using).filter(product_id=product.pk):
            existing_item = CartItem.objects.using(using).filter(
                cart_id=item.cart_id,
                product_id=target.pk,
            ).first()
            if existing_item:
                existing_item.quantity += item.quantity
                existing_item.save(using=using, update_fields=['quantity'])
                item.delete(using=using)
            else:
                item.product_id = target.pk
                item.save(using=using, update_fields=['product'])

        Product.objects.using(using).filter(pk=product.pk).update(
            is_active=False,
            stock_quantity=0,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0025_order_checkout_discount'),
    ]

    operations = [
        migrations.RunPython(discount_and_scope_products, migrations.RunPython.noop),
    ]
