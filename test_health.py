from app.health_manager import HealthManager

health = HealthManager()

print(health.check("http://localhost:8500"))
print(health.check("http://localhost:5076"))
print(health.check("http://localhost:3600"))
print(health.check("http://localhost:3500"))