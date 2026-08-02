import json


class ConfigManager:

    def __init__(self):
        self.config = {}

    def load(self):
        with open("config/settings.json", "r") as file:
            self.config = json.load(file)

    def get(self, key):
        return self.config.get(key)