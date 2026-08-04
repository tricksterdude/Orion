from app.display.controller import DisplayController

controller = DisplayController()

tests = [
    23.976,
    24.000,
    25.000,
    29.970,
    30.000,
    50.000,
    59.940,
    60.000,
]

print()
print("DISPLAY CONTROLLER")
print("------------------")

for fps in tests:

    refresh = controller.choose_refresh(fps)

    print(f"{fps:.3f} fps  ->  {refresh} Hz")