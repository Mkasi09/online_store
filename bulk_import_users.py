import json
from pathlib import Path
from django.core import serializers
from django.contrib.auth import get_user_model
from django.db import transaction, connection
from django.db.models import Count
from django.core.management.color import no_style

source = Path("sqlite_backup_pk_utf8.json")

with source.open("r", encoding="utf-8") as f:
    data = json.load(f)

user_records = [
    item for item in data
    if item["model"] == "auth.user"
]

User = get_user_model()

print("Users to import:", len(user_records))
print("Existing users:", User.objects.count())

if User.objects.exists():
    raise Exception("Users already exist. Stopping to prevent duplicates.")

deserialized = serializers.deserialize(
    "json",
    json.dumps(user_records, ensure_ascii=False)
)

objects = [item.object for item in deserialized]

with transaction.atomic():
    for start in range(0, len(objects), 1000):
        batch = objects[start:start + 1000]
        User.objects.bulk_create(batch, batch_size=1000)
        print("Imported:", min(start + 1000, len(objects)))

    with connection.cursor() as cursor:
        for sql in connection.ops.sequence_reset_sql(no_style(), [User]):
            cursor.execute(sql)

print("SUCCESS!")
print("Total users:", User.objects.count())
