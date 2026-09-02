import ctypes
import os


MUTEX_NAME = "Local\\OrionHomeCinema"
ERROR_ALREADY_EXISTS = 183


def acquire_single_instance():

    if os.name != "nt":

        return True

    kernel32 = ctypes.windll.kernel32

    handle = kernel32.CreateMutexW(
        None,
        False,
        MUTEX_NAME,
    )

    if not handle:

        raise ctypes.WinError()

    if kernel32.GetLastError() == (
        ERROR_ALREADY_EXISTS
    ):

        kernel32.CloseHandle(handle)
        return None

    return handle


def release_single_instance(handle):

    if handle is None or os.name != "nt":

        return

    ctypes.windll.kernel32.CloseHandle(handle)
