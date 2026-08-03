from app.reports.report import OrionReport


class ReportManager:

    def build(self, system, services):

        report = OrionReport()

        report.system = system

        report.services = services

        total = len(services)

        healthy = 0

        excellent = 0

        good = 0

        slow = 0

        offline = 0

        for service in services:

            if service.healthy:
                healthy += 1

            if service.response_time is None:
                offline += 1

            elif service.response_time < 50:
                excellent += 1

            elif service.response_time < 150:
                good += 1

            else:
                slow += 1

        report.statistics = {

            "total": total,

            "healthy": healthy,

            "excellent": excellent,

            "good": good,

            "slow": slow,

            "offline": offline

        }

        report.overall_health = round(
            (healthy / total) * 100
        )

        return report