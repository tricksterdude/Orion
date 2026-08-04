from app.display.restore import DisplayRestore
from app.display.adapter import DisplayAdapter

adapter = DisplayAdapter()
restore = DisplayRestore()

mode = adapter.current_mode()

restore.save(mode)

print()
print("RESTORE INFORMATION")
print("-------------------")

print(restore.current())