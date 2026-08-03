class Service:

    def __init__(self, name, container, port, url):

        self.name = name
        self.container = container
        self.port = port
        self.url = url

        self.running = False
        self.healthy = False

        self.response_time = None
        self.status_code = None

    def __str__(self):

        status = "Running" if self.running else "Stopped"

        return f"{self.name} ({status})"