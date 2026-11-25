import json
from pathlib import Path
from django.core import serializers
from django.apps import apps
from django.db import transaction, connection
from django.core.management.color import no_style
from django.contrib.auth import get_user_model

source = Path("sqlite_backup_pk_utf8.json")

with source.open("r", encoding="utf-8-sig") as f:
    data = json.load(f)

# Import order respects foreign-key dependencies.
order = [
    "iphonemodel",
    "color",
    "iphoneproduct",
    "productreview",
    "cart",
    "cartitem",
    "order",
    "orderitem",
    "pendingorder",
]

User = get_user_model()

if User.objects.count() != 22512:
    raise Exception("User count is not 22512. Stopping.")

models_by_name = {
    model._meta.model_name: model
    for model in apps.get_app_config("store").get_models()
}

print("Starting remaining store data import...")

with transaction.atomic():

    imported_models = []

    for name in order:
        model = models_by_name[name]

        records = [
            item for item in data
            if item["model"] == f"store.{name}"
        ]

        if model.objects.exists():
            raise Exception(
                f"{model.__name__} already contains records. Stopping."
            )

        if not records:
            print(f"{name}: no records")
            continue

        objects = [
            item.object
            for item in serializers.deserialize(
                "json",
                json.dumps(records, ensure_ascii=False)
            )
        ]

        for start in range(0, len(objects), 500):
            batch = objects[start:start + 500]
            model.objects.bulk_create(batch, batch_size=500)

        imported_models.append(model)

        print(f"{model.__name__}: {len(objects)} imported")

    # Reset ID sequences for imported models.
    with connection.cursor() as cursor:
        for sql in connection.ops.sequence_reset_sql(
            no_style(), imported_models
        ):
            cursor.execute(sql)

print("\nSTORE DATA IMPORT SUCCESSFUL!")

for name in order:
    model = models_by_name[name]
    print(f"{model.__name__}: {model.objects.count()}")

print("Users:", User.objects.count())
