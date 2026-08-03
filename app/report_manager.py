from app.reports.report import OrionReport
from app.diagnostics import Diagnostics


class ReportManager:

    def build(self, system, services):

        diagnostics = Diagnostics()

        report = OrionReport()

        report.system = system
        report.services = services

        healthy = 0
        excellent = 0
        good = 0
        slow = 0
        offline = 0

        for service in services:

            if service.healthy:
                healthy += 1

            result = diagnostics.evaluate(service)

            if result["rating"] == "Excellent":
                excellent += 1

            elif result["rating"] == "Good":
                good += 1

            elif result["rating"] == "Slow":
                slow += 1

            else:
                offline += 1

        total = len(services)

        report.statistics = {
            "healthy": healthy,
            "total": total,
            "excellent": excellent,
            "good": good,
            "slow": slow,
            "offline": offline
        }

        report.overall_health = round((healthy / total) * 100) if total else 0

        return report