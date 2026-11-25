import json
from pathlib import Path

source = Path("sqlite_backup_pk.json")
target = Path("sqlite_backup_pk_utf8.json")

raw = source.read_bytes()
data = json.loads(raw.decode("cp1252"))

with target.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

print("Conversion successful!")
print("Records:", len(data))
print("New file size:", target.stat().st_size)
