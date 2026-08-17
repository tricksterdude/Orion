import re
import requests

BASE = "http://127.0.0.1:3500"

print("=" * 60)
print("AIOSTREAMS FRONTEND")
print("=" * 60)

html = requests.get(BASE, timeout=5).text

print(f"\nDownloaded {len(html)} bytes")

scripts = re.findall(r'<script[^>]+src="([^"]+)"', html)

print("\nJavaScript files:\n")

for script in scripts:
    print(script)