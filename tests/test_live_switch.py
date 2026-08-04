from app.display.adapter import DisplayAdapter

adapter = DisplayAdapter()

print()
print("LIVE SWITCH TEST")
print("----------------")

print("Current Mode")

print(adapter.current_mode())

print()

print("Target")

print({
    "width": 3840,
    "height": 2160,
    "bits": 32,
    "refresh": 60
})