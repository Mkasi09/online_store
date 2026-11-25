from pathlib import Path
import json

source = Path("sqlite_backup.json")
target = Path("sqlite_backup_utf8.json")

# Read the original Windows-encoded export
raw = source.read_bytes()
text = raw.decode("cp1252")

# Check that the file contains valid JSON before converting
data = json.loads(text)

# Save a new UTF-8 version
target.write_text(text, encoding="utf-8")

print("Conversion successful!")
print("Records exported:", len(data))
print("New file:", target)
print("File size:", target.stat().st_size)
