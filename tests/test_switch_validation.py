from app.display.switcher import DisplaySwitcher

switcher = DisplaySwitcher()

target = {
    "width": 3840,
    "height": 2160,
    "bits": 32,
    "refresh": 23,
}

print()
print("DISPLAY SWITCH TEST")
print("-------------------")

print(
    "Validation:",
    switcher.test_switch(target)
)