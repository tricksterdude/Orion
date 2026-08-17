import ctypes

CDS_TEST = 0x00000002

result = ctypes.windll.user32.ChangeDisplaySettingsW(
    None,
    CDS_TEST
)

print()
print("DISPLAY API TEST")
print("----------------")
print("Return Code:", result)