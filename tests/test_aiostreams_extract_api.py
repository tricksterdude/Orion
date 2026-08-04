import re
import requests

url = "http://127.0.0.1:3000/assets/js/index.ecd59f14.js"

print("=" * 60)
print("AIOSTREAMS FETCH EXTRACTOR")
print("=" * 60)

text = requests.get(url).text

print(f"Downloaded {len(text):,} bytes\n")

patterns = [
    r"fetch\([^)]{0,300}\)",
    r"/api[^\"'` )]+",
]

matches = set()

for pattern in patterns:
    for match in re.findall(pattern, text):
        matches.add(match)

print(f"Found {len(matches)} matches\n")

for match in sorted(matches):
    print("-" * 60)
    print(match)