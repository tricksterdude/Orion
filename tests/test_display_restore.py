import time

from app.display.restore import DisplayRestore
from app.display.mode import DisplayMode
from app.display.switcher import DisplaySwitcher

restore = DisplayRestore()
switcher = DisplaySwitcher()

restore.save()

print()
print("=" * 60)
print("DISPLAY RESTORE TEST")
print("=" * 60)

print()
print("Saved mode:")
print(restore.original_mode())

target = DisplayMode(
    width=restore.original.width,
    height=restore.original.height,
    bits=restore.original.bits,
    refresh=60,
)

print()
print("Switching to 60 Hz...")

print("Success:", switcher.switch(target))

time.sleep(5)

print()
print("Restoring...")

print("Success:", restore.restore())

print()
print("Current mode:")

print(switcher.adapter.current_mode())