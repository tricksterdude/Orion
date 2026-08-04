from app.display.switcher import DisplaySwitcher

switcher = DisplaySwitcher()

tests = [
    (3840, 2160, 23),
    (3840, 2160, 24),
    (3840, 2160, 50),
    (3840, 2160, 60),
    (3840, 2160, 120),
    (3840, 2160, 144),
]

print()
print("DISPLAY SWITCH VALIDATION")
print("-------------------------")

for width, height, refresh in tests:

    supported = switcher.can_switch(
        width,
        height,
        refresh
    )

    print(
        f"{width}x{height} @ {refresh} Hz : {supported}"
    )