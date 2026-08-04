import requests

BASE = "http://127.0.0.1:11470"

paths = [
    "/",
    "/manifest.json",
    "/stremio/v1",
    "/stremio",
    "/streaming",
    "/streams",
    "/player",
    "/playback",
    "/api",
    "/api/",
    "/api/v1",
    "/addons",
    "/shell",
]

print("=" * 60)
print("STREMIO ENDPOINT PROBE")
print("=" * 60)

for path in paths:

    try:

        r = requests.get(BASE + path, timeout=2)

        print()
        print(path)
        print(r.status_code)
        print(r.headers.get("Content-Type"))

    except Exception as ex:

        print()
        print(path)
        print(ex)