from app.config_manager import ConfigManager


config = ConfigManager()

print("=" * 60)
print("CONFIG MANAGER")
print("=" * 60)
print()

print("Application :", config.get("application"))
print("Author      :", config.get("author"))
print("TMDb Found  :", bool(config.get("tmdb.api_key")))
print("Key Length  :", len(config.get("tmdb.api_key")))