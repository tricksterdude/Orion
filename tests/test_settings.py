from app.config.settings import settings


print("=" * 60)
print("SETTINGS")
print("=" * 60)

print()

print("Application :", settings.application)
print("Author      :", settings.author)
print("TMDb Key    :", "*" * len(settings.tmdb_api_key))
print("Key Length  :", len(settings.tmdb_api_key))