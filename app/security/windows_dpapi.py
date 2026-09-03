import ctypes
import os
from ctypes import wintypes


class DataProtectionError(RuntimeError):
    pass


class _DataBlob(ctypes.Structure):

    _fields_ = [
        ("size", wintypes.DWORD),
        ("data", ctypes.POINTER(ctypes.c_byte)),
    ]


class WindowsDataProtector:

    UI_FORBIDDEN = 0x1

    def __init__(self, description="Orion private settings"):

        self.description = description

    @staticmethod
    def _blob(value):

        buffer = ctypes.create_string_buffer(value)

        return (
            _DataBlob(
                len(value),
                ctypes.cast(
                    buffer,
                    ctypes.POINTER(ctypes.c_byte),
                ),
            ),
            buffer,
        )

    def protect(self, value):

        if os.name != "nt":
            raise DataProtectionError(
                "Windows secure storage is unavailable."
            )

        source, source_buffer = self._blob(value)
        output = _DataBlob()

        success = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(source),
            ctypes.c_wchar_p(self.description),
            None,
            None,
            None,
            self.UI_FORBIDDEN,
            ctypes.byref(output),
        )

        del source_buffer

        if not success:
            raise ctypes.WinError()

        try:
            return ctypes.string_at(
                output.data,
                output.size,
            )
        finally:
            ctypes.windll.kernel32.LocalFree(
                output.data
            )

    def unprotect(self, value):

        if os.name != "nt":
            raise DataProtectionError(
                "Windows secure storage is unavailable."
            )

        source, source_buffer = self._blob(value)
        output = _DataBlob()

        success = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(source),
            None,
            None,
            None,
            None,
            self.UI_FORBIDDEN,
            ctypes.byref(output),
        )

        del source_buffer

        if not success:
            raise ctypes.WinError()

        try:
            return ctypes.string_at(
                output.data,
                output.size,
            )
        finally:
            ctypes.windll.kernel32.LocalFree(
                output.data
            )
