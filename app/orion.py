from app.health_manager import HealthManager
from app.diagnostics import Diagnostics
from app.logger import Logger
from app.config_manager import ConfigManager
from app.service_manager import ServiceManager
from app.docker_manager import DockerManager
from app.system_manager import SystemManager
from app.report_manager import ReportManager
from app.dashboard import Dashboard
from app.menu import Menu
from app.banner import Banner
from app.service_view import ServiceView
from config.version import VERSION


class Orion:

    def __init__(self):
        self.config = ConfigManager()
        self.logger = Logger()
        self.services = ServiceManager()
        self.docker = DockerManager()
        self.system = SystemManager()
        self.health = HealthManager()
        self.diagnostics = Diagnostics()
        self.report_manager = ReportManager()
        self.dashboard = Dashboard()
        self.menu = Menu()
        self.banner = Banner()
        self.service_view = ServiceView()

    def start(self):

        while True:

            self.load_configuration()
            self.load_services()
            self.check_services()

            system = {
                "computer": self.system.get_hostname(),
                "os": f"{self.system.get_os()} {self.system.get_release()}",
                "python": self.system.get_python_version(),
                "cpu": self.system.get_cpu_usage(),
                "memory": self.system.get_memory_usage(),
                "disk": self.system.get_disk_usage()
            }

            report = self.report_manager.build(
                system,
                self.services.get_all()
            )

            self.banner.show()
            self.dashboard.show(report, self.logger)

            choice = self.menu.show()

            if choice == "1":
                continue

            elif choice == "2":
                self.service_menu()

            elif choice == "3":
                continue

            elif choice == "0":
                self.logger.log("Goodbye.")
                break

            else:
                self.logger.log("Invalid option.")

    def load_configuration(self):
        self.config.load()

    def load_services(self):
        self.services = ServiceManager()
        self.services.register_defaults()

    def check_services(self):

        for service in self.services.get_all():

            service.running = self.docker.is_running(service.container)

            if service.running:

                result = self.health.check(service.url)

                service.healthy = result["healthy"]
                service.status_code = result["status_code"]
                service.response_time = result["response_time"]

            else:

                service.healthy = False
                service.status_code = None
                service.response_time = None

    def service_menu(self):

        while True:

            services = self.services.get_all()

            choice = self.service_view.show_list(services)

            if choice == "0":
                return

            try:
                service = services[int(choice) - 1]
            except (ValueError, IndexError):
                self.logger.log("Invalid selection.")
                continue

            self.service_view.show_service(
                service,
                self.docker,
                self.diagnostics,
                self.logger
            )