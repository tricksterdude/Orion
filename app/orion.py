from app.logger import Logger
from app.config_manager import ConfigManager
from app.service_manager import ServiceManager


class Orion:

    def __init__(self):
        self.config = ConfigManager()
        self.logger = Logger()
        self.services = ServiceManager()

    def start(self):
        self.load_configuration()
        self.load_services()
        self.display_startup()

    def load_configuration(self):
        self.config.load()

    def load_services(self):
        self.services.register_defaults()

    def display_startup(self):

        self.logger.log("Starting Orion...")
        self.logger.log(f"Version: {self.config.get('version')}")
        self.logger.log(f"Application: {self.config.get('application')}")
        self.logger.log(f"Author: {self.config.get('author')}")

        print()
        print("=" * 50)
        print("REGISTERED SERVICES")
        print("=" * 50)

        for service in self.services.get_all():
            self.logger.log(str(service))

        print()
        self.logger.log("System Ready.")