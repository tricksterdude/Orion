import webbrowser


class ServiceView:

    def show_list(self, services):

        print()
        print("=" * 60)
        print("                     SERVICES")
        print("=" * 60)

        for index, service in enumerate(services, start=1):
            print(f"{index}. {service.name}")

        print()
        print("0. Back")
        print()

        return input("Choice: ")

    def show_service(self, service, docker, diagnostics, logger):

        while True:

            print()
            print("=" * 60)
            print(service.name)
            print("=" * 60)

            diagnostics_result = diagnostics.evaluate(service)
            stats = docker.stats(service.container)

            logger.log(f"Container       : {service.container}")
            logger.log(f"Port            : {service.port}")
            logger.log(
                f"Health          : {'Healthy' if service.healthy else 'Unhealthy'}"
            )
            logger.log(f"HTTP Status     : {service.status_code}")
            logger.log(f"Response Time   : {service.response_time} ms")

            logger.log("")
            logger.log("Docker Statistics")
            logger.log("-----------------")
            logger.log(f"CPU Usage       : {stats['cpu']}")
            logger.log(f"Memory Usage    : {stats['memory']}")

            logger.log("")
            logger.log(f"Rating          : {diagnostics_result['rating']}")
            logger.log(
                f"Recommendation  : {diagnostics_result['recommendation']}"
            )

            print()
            print("1. Restart Container")
            print("2. Stop Container")
            print("3. Start Container")
            print("4. View Logs")
            print("5. Open Web UI")
            print("0. Back")
            print()

            choice = input("Choice: ")

            if choice == "1":

                docker.restart(service.container)
                logger.log("Container restarted.")
                input("Press ENTER...")

            elif choice == "2":

                docker.stop(service.container)
                logger.log("Container stopped.")
                input("Press ENTER...")

            elif choice == "3":

                docker.start(service.container)
                logger.log("Container started.")
                input("Press ENTER...")

            elif choice == "4":

                print()
                print("=" * 60)
                print("LAST 50 LOG LINES")
                print("=" * 60)
                print()

                print(docker.logs(service.container))

                input("Press ENTER...")

            elif choice == "5":

                logger.log(f"Opening {service.url}")
                webbrowser.open(service.url)

                input("Press ENTER...")

            elif choice == "0":

                return

            else:

                logger.log("Invalid option.")