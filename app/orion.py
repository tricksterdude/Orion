from app.logger import Logger
from app.config_manager import ConfigManager
from app.service_manager import ServiceManager
from app.docker_manager import DockerManager
from app.system_manager import SystemManager
from config.version import VERSION


class Orion:

    def __init__(self):
        self.config = ConfigManager()
        self.logger = Logger()
        self.services = ServiceManager()
        self.docker = DockerManager()
        self.system = SystemManager()

    def start(self):
        self.load_configuration()
        self.load_services()
        self.check_services()
        self.display_startup()

    def load_configuration(self):
        self.config.load()

    def load_services(self):
        self.services.register_defaults()

    def check_services(self):
        for service in self.services.get_all():
            service.running = self.docker.is_running(service.container)

    def display_startup(self):

        self.logger.log("Starting Orion...")
        self.logger.log(f"Version: {VERSION}")
        self.logger.log(f"Application: {self.config.get('application')}")
        self.logger.log(f"Author: {self.config.get('author')}")

        print()
        print("=" * 50)
        print("SYSTEM")
        print("=" * 50)

        self.logger.log(f"Computer : {self.system.get_hostname()}")
        self.logger.log(
            f"OS       : {self.system.get_os()} {self.system.get_release()}"
        )
        self.logger.log(
            f"Python   : {self.system.get_python_version()}"
        )

        print()
        print("=" * 50)
        print("SERVICE STATUS")
        print("=" * 50)

        for service in self.services.get_all():

            if service.running:
                icon = "✓"
                status = "Running"
            else:
                icon = "✗"
                status = "Stopped"

            self.logger.log(
                f"{icon} {service.name:<18} {status:<8} Port {service.port}"
            )

        print()
        self.logger.log("System Ready.")