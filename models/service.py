class Service:

    def __init__(self, name, container, port):
        self.name = name
        self.container = container
        self.port = port
        self.running = False
        self.healthy = False

    def __str__(self):
        status = "Running" if self.running else "Stopped"
        return f"{self.name} ({status}) - Port {self.port}"