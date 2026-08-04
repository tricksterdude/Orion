from app.display.adapter import DisplayAdapter

adapter = DisplayAdapter()

print()
print("4K CINEMA MODES")
print("----------------")

for mode in adapter.cinema_modes():

    print(f"{mode.refresh} Hz")