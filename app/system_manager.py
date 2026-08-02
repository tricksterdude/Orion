import platform
import socket


class SystemManager:

    def get_hostname(self):
        return socket.gethostname()

    def get_os(self):
        return platform.system()

    def get_release(self):
        return platform.release()

    def get_python_version(self):
        return platform.python_version()