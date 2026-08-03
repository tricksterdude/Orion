class Inspector:

    def show(self, docker, diagnostics, service, logger):

        data = docker.inspect(service.container)

        if data is None:
            logger.log(f"{service.name}: No information available")
            return

        report = diagnostics.evaluate(service)

        logger.log(service.name)
        logger.log(f"    Image          : {data['Config']['Image']}")
        logger.log(f"    Status         : {data['State']['Status']}")
        logger.log(f"    Health         : {'Healthy' if service.healthy else 'Unavailable'}")
        logger.log(f"    HTTP Status    : {service.status_code}")
        logger.log(f"    Response Time  : {service.response_time} ms")
        logger.log(f"    Rating         : {report['rating']}")
        logger.log(f"    Recommendation : {report['recommendation']}")
        logger.log("")