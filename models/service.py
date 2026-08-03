class Service:

    def __init__(self, name, container, port, url):

        self.name = name
        self.container = container
        self.port = port
        self.url = url

        self.running = False
        self.healthy = False
        self.status_code = 0
        self.response_time = 0