from ui.screen import Screen


class Dashboard(Screen):

    def show(self, report, alerts, logger):

        self.title("SYSTEM STATUS")

        logger.log(f" Overall Health    : {report.overall_health}%")
        logger.log("")

        logger.log(f" Computer          : {report.system['computer']}")
        logger.log(f" Operating System  : {report.system['os']}")
        logger.log(f" Python            : {report.system['python']}")

        print()

        logger.log(f" CPU Usage         : {report.system['cpu']}%")
        logger.log(f" Memory Usage      : {report.system['memory']}%")
        logger.log(f" Disk Usage        : {report.system['disk']}%")

        print()

        logger.log(
            f" Healthy Services  : {report.statistics['healthy']} / {report.statistics['total']}"
        )
        logger.log(f" Excellent         : {report.statistics['excellent']}")
        logger.log(f" Good              : {report.statistics['good']}")
        logger.log(f" Slow              : {report.statistics['slow']}")
        logger.log(f" Offline           : {report.statistics['offline']}")

        print()
        self.title("ALERTS")

        if not alerts:

            self.success("✓ No alerts")
            print("System operating normally.")

        else:

            for alert in alerts:
                self.warning(f"⚠ {alert}")

        print()