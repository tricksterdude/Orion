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
from app.alert_manager import AlertManager
from app.refresh_manager import RefreshManager
from app.about import About
from app.doctor import OrionDoctor
from app.doctor_view import DoctorView
from app.hardware_manager import HardwareManager
from app.hardware_view import HardwareView
from app.display_manager import DisplayManager
from app.display_view import DisplayView


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
        self.alert_manager = AlertManager()
        self.refresh_manager = RefreshManager()
        self.about = About()

        self.doctor = OrionDoctor()
        self.doctor_view = DoctorView()

        self.hardware_manager = HardwareManager()
        self.hardware_view = HardwareView()

        self.display_manager = DisplayManager()
        self.display_view = DisplayView()

    def start(self):

        while True:

            report, alerts = self.refresh_manager.refresh(self)

            self.banner.show()

            self.dashboard.show(
                report,
                alerts,
                self.logger
            )

            choice = self.menu.show()

            if choice == "1":

                continue

            elif choice == "2":

                self.service_menu()

            elif choice == "3":

                continue

            elif choice == "4":

                self.about.show()

            elif choice == "5":

                results = self.doctor.run(report)
                self.doctor_view.show(results)

            elif choice == "6":

                hardware = self.hardware_manager.summary()
                self.hardware_view.show(hardware)

            elif choice == "7":

                display = self.display_manager.summary()
                self.display_view.show(display)

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