class Dashboard:

    def show(self, report, logger):

        print("┌" + "─" * 58 + "┐")
        print("│                    SYSTEM STATUS                    │")
        print("├" + "─" * 58 + "┤")

        logger.log(f" Overall Health    : {report.overall_health}%")
        logger.log("")

        logger.log(f" Computer          : {report.system['computer']}")
        logger.log(f" Operating System  : {report.system['os']}")
        logger.log(f" Python            : {report.system['python']}")

        logger.log("")
        print("├" + "─" * 58 + "┤")

        logger.log(f" CPU Usage         : {report.system['cpu']}%")
        logger.log(f" Memory Usage      : {report.system['memory']}%")
        logger.log(f" Disk Usage        : {report.system['disk']}%")

        logger.log("")
        print("├" + "─" * 58 + "┤")

        logger.log(
            f" Healthy Services  : {report.statistics['healthy']} / {report.statistics['total']}"
        )
        logger.log(f" Excellent         : {report.statistics['excellent']}")
        logger.log(f" Good              : {report.statistics['good']}")
        logger.log(f" Slow              : {report.statistics['slow']}")
        logger.log(f" Offline           : {report.statistics['offline']}")

        print("└" + "─" * 58 + "┘")
        print()