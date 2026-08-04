import requests
import re

url = "http://127.0.0.1:3000/assets/js/index.ecd59f14.js"

print("=" * 60)
print("AIOSTREAMS JAVASCRIPT")
print("=" * 60)

text = requests.get(url).text

print(f"\nDownloaded {len(text):,} bytes")

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