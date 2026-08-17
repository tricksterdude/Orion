from app.display.mode import DisplayMode
from app.display.switcher import DisplaySwitcher

switcher = DisplaySwitcher()

target = DisplayMode(
    width=3840,
    height=2160,
    bits=32,
    refresh=23,
)

print()
print("DISPLAY SWITCH TEST")
print("-------------------")

print("Validation:", switcher.test_switch(target))