import json
from collections import Counter

with open("sqlite_backup_utf8.json", encoding="utf-8") as f:
    data = json.load(f)

users = [x for x in data if x["model"] == "auth.user"]

print("USER RECORDS:", len(users))
print("USER FIELD NAMES:", list(users[0]["fields"].keys()))

for field in ["groups", "user_permissions"]:
    counts = Counter(len(x["fields"].get(field, [])) for x in users)
    print(f"\n{field.upper()} DISTRIBUTION:")
    for count, users_count in sorted(counts.items()):
        print(f"{count} relationships: {users_count} users")

print("\nFIRST USER RECORD:")
print(json.dumps(users[0], indent=2)[:2000])
