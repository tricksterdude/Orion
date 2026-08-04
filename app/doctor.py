class OrionDoctor:

    def run(self, report):

        results = []

        if report.system["cpu"] < 90:
            results.append(("PASS", "CPU usage is normal"))
        else:
            results.append(("WARNING", "High CPU usage detected"))

        if report.system["memory"] < 80:
            results.append(("PASS", "Memory usage is normal"))
        else:
            results.append(("WARNING", "High memory usage detected"))

        if report.system["disk"] < 90:
            results.append(("PASS", "Disk usage is normal"))
        else:
            results.append(("WARNING", "Disk usage is high"))

        for service in report.services:

            if service.running and service.healthy:
                results.append(("PASS", f"{service.name} is healthy"))
            elif not service.running:
                results.append(("FAIL", f"{service.name} is offline"))
            else:
                results.append(("WARNING", f"{service.name} is unhealthy"))

        return results