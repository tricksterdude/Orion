from app.cinema.engine import CinemaEngine

engine = CinemaEngine()

result = engine.analyse(23.976)

print()
print("=" * 60)
print("             ORION CINEMA ENGINE")
print("=" * 60)
print()

print(f"Movie FPS : {result['fps']:.3f}")
print()

print(
    f"Current : "
    f"{result['current'].width}x"
    f"{result['current'].height} @ "
    f"{result['current'].refresh} Hz"
)

print(
    f"Target  : "
    f"{result['target'].width}x"
    f"{result['target'].height} @ "
    f"{result['target'].refresh} Hz"
)

print()

print(f"Supported : {result['supported']}")
print(f"Simulation: {result['simulation']}")

print()

if result["supported"]:
    print("✓ Orion would perform this switch.")
else:
    print("✗ Requested mode unavailable.")