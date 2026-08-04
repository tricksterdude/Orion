import time

from app.display.adapter import DisplayAdapter
from app.display.mode import DisplayMode
from app.display.switcher import DisplaySwitcher

adapter = DisplayAdapter()
switcher = DisplaySwitcher()

original = adapter.current_mode()

print()
print("ORIGINAL")
print(original)

target = DisplayMode(
    width=original.width,
    height=original.height,
    bits=original.bits,
    refresh=60,
)

print()
print("SWITCHING TO 60 Hz...")

success = switcher.switch(target)

print("Success:", success)

time.sleep(5)

print()
print("RESTORING...")

switcher.switch(original)

print("DONE")