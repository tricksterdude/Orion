class RefreshManager:

    def refresh(self, orion):

        orion.load_configuration()
        orion.load_services()
        orion.check_services()

        system = {
            "computer": orion.system.get_hostname(),
            "os": f"{orion.system.get_os()} {orion.system.get_release()}",
            "python": orion.system.get_python_version(),
            "cpu": orion.system.get_cpu_usage(),
            "memory": orion.system.get_memory_usage(),
            "disk": orion.system.get_disk_usage()
        }

        report = orion.report_manager.build(
            system,
            orion.services.get_all()
        )

        alerts = orion.alert_manager.build(report)

        return report, alerts