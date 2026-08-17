import re

import requests


BASE = "http://127.0.0.1:3500"

print("=" * 60)
print("AIOSTREAMS FETCH EXTRACTOR")
print("=" * 60)

html = requests.get(
    BASE,
    timeout=5,
).text

scripts = re.findall(
    r'<script[^>]+src="([^"]+)"',
    html,
)

index_script = next(
    script
    for script in scripts
    if "/index." in script
)

url = BASE + index_script

text = requests.get(
    url,
    timeout=10,
).text

print(f"JavaScript: {index_script}")
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