from app.config_manager import ConfigManager


config = ConfigManager()

print("=" * 60)
print("CONFIG MANAGER")
print("=" * 60)
print()

print("Application :", config.get("application"))
print("Author      :", config.get("author"))
tmdb_key = config.get("tmdb.api_key", "")
print("TMDb Found  :", bool(tmdb_key))
print("Key Length  :", len(tmdb_key))
