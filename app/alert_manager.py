class AlertManager:

    def build(self, report):

        alerts = []

        if report.system["memory"] >= 80:
            alerts.append("Memory usage is above 80%")

        if report.system["cpu"] >= 90:
            alerts.append("CPU usage is above 90%")

        if report.system["disk"] >= 90:
            alerts.append("Disk usage is above 90%")

        for service in report.services:

            if not service.running:
                alerts.append(f"{service.name} is offline")

            elif service.response_time is not None:

                if service.response_time >= 500:
                    alerts.append(
                        f"{service.name} response time is high"
                    )

        return alerts