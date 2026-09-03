import json

from app.local_configuration import services_config_path
from models.service import Service


class ServiceManager:

    def __init__(self):
        self.services = []

    def register_defaults(self):

        self.services.clear()

        with services_config_path().open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        for item in data["services"]:

            self.services.append(
                Service(
                    item["name"],
                    item["container"],
                    item["port"],
                    item["url"]
                )
            )

    def get_all(self):
        return self.services
