from app.health_manager import HealthManager

health = HealthManager()

print(health.check("http://localhost:8080"))
print(health.check("http://localhost:5076"))
print(health.check("http://localhost:3232"))
print(health.check("http://localhost:3000"))