import platform
import socket
import sys
import psutil


class SystemManager:

    def get_hostname(self):
        return socket.gethostname()

    def get_os(self):
        return platform.system()

    def get_release(self):
        return platform.release()

    def get_python_version(self):
        return platform.python_version()

    def get_cpu_usage(self):
        return round(psutil.cpu_percent(interval=0.5), 1)

    def get_memory_usage(self):
        return round(psutil.virtual_memory().percent, 1)

    def get_disk_usage(self):
        return round(psutil.disk_usage("/").percent, 1)