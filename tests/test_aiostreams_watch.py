import time

from app.providers.aiostreams import AIOStreamsProvider


print("=" * 60)
print("AIOSTREAMS WATCHER")
print("=" * 60)
print()

provider = AIOStreamsProvider()

provider.start()

print("Waiting for AIOStreams events...")
print("Choose a movie in Stremio.")
print()

while True:
    time.sleep(1)