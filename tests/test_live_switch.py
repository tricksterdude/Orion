import time

from app.display.adapter import DisplayAdapter
from app.display.mode import DisplayMode
from app.display.switcher import DisplaySwitcher

adapter = DisplayAdapter()
switcher = DisplaySwitcher()

original = adapter.current_mode()

print()
print("=" * 60)
print("ORION LIVE DISPLAY SWITCH TEST")
print("=" * 60)
print()

print("Original:")
print(original)

target = DisplayMode(
    width=original.width,
    height=original.height,
    bits=original.bits,
    refresh=60,
)

try:

    print()
    print("Switching to 60 Hz...")

    success = switcher.switch(target)

    print("Switch result:", success)

    current = adapter.current_mode()

    print("Current mode:", current)

    print()
    print("Waiting 5 seconds...")

    time.sleep(5)

finally:

    print()
    print("Restoring original mode...")

    switcher.switch(original)

    print("Restored.")

    current = adapter.current_mode()

    print("Current mode:", current)