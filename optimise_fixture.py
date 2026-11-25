import json
from pathlib import Path

source = Path("sqlite_backup_utf8.json")
target = Path("sqlite_backup_optimized.json")

with source.open("r", encoding="utf-8") as f:
    data = json.load(f)

removed = 0

for item in data:
    if item["model"] == "auth.user":
        fields = item["fields"]
        fields.pop("groups", None)
        fields.pop("user_permissions", None)
        removed += 1

with target.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

print("Optimised fixture created.")
print("User records:", removed)
print("Total records:", len(data))
print("File size:", target.stat().st_size)
print("File:", target)
