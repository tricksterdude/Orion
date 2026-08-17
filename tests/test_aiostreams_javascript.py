import re

import requests


BASE = "http://127.0.0.1:3500"

print("=" * 60)
print("AIOSTREAMS JAVASCRIPT")
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

print(f"\nJavaScript: {index_script}")
print(f"Downloaded {len(text):,} bytes")

keywords = [
    "/api",
    "fetch(",
    "axios",
    "graphql",
    "socket",
    "websocket",
    "ws://",
    "wss://",
    "stream",
    "playback",
    "player",
    "localhost",
    "3000",
]

print("\nSearching...\n")

for keyword in keywords:

    if keyword.lower() in text.lower():

        print(f"✓ {keyword}")

    else:

        print(f"✗ {keyword}")