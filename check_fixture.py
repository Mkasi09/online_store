import json
from collections import Counter

with open("sqlite_backup_utf8.json", encoding="utf-8") as f:
    data = json.load(f)

counts = Counter(item["model"] for item in data)

print("TOTAL RECORDS:", len(data))
print("\nRECORDS PER MODEL:")
for model, count in counts.most_common():
    print(f"{model}: {count}")

print("\nLARGEST MANY-TO-MANY RELATIONSHIPS:")
for item in data:
    fields = item.get("fields", {})
    for name, value in fields.items():
        if isinstance(value, list) and len(value) > 20:
            print(item["model"], item["pk"], name, "=", len(value))
