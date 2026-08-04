import requests

BASE = "http://127.0.0.1:3000"

endpoints = [
    "/api/v1/dashboard/system/stream",
    "/api/v1/dashboard/usenet/live/stream",
    "/api/v1/dashboard/usenet/library/stream",
    "/api/v1/dashboard/logs/stream",
]

print("=" * 60)
print("AIOSTREAMS API TEST")
print("=" * 60)

session = requests.Session()

for endpoint in endpoints:

    print()
    print("=" * 60)
    print(endpoint)
    print("=" * 60)

    try:

        response = session.get(
            BASE + endpoint,
            stream=True,
            timeout=5,
        )

        print("Status:", response.status_code)
        print("Content-Type:", response.headers.get("Content-Type"))

        for i, line in enumerate(response.iter_lines()):

            if line:

                print(line.decode(errors="ignore"))

            if i == 10:
                break

    except Exception as ex:

        print(ex)