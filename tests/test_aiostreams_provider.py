from app.providers.aiostreams import AIOStreamsProvider


print("=" * 60)
print("AIOSTREAMS PROVIDER")
print("=" * 60)
print()

provider = AIOStreamsProvider()

print(f"Name       : {provider.name}")
print(f"Available  : {provider.is_available()}")
print(f"Media      : {provider.current_media()}")