import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

from app.health_manager import HealthManager


class ServiceStatus:

    def __init__(
        self,
        service_manager=None,
        health_manager=None,
    ):

        self.service_manager = (
            service_manager
        )

        if service_manager is None:

            self.services = (
                self._load_configured_services()
            )

        else:

            self.services = (
                service_manager.get_all()
            )

        if health_manager is None:

            health_manager = HealthManager()

        self.health = health_manager

    @staticmethod
    def _load_configured_services():

        project_root = (
            Path(__file__).resolve().parents[2]
        )

        config_path = (
            project_root
            / "config"
            / "services.json"
        )

        with config_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return [
            SimpleNamespace(**service)
            for service in data["services"]
        ]

    def reload(self):

        if self.service_manager is None:

            self.services = (
                self._load_configured_services()
            )

        else:

            self.services = (
                self.service_manager.get_all()
            )

        return self.services

    @staticmethod
    def _slug(name):

        return "".join(
            character.lower()
            for character in name
            if character.isalnum()
        )

    def _check(self, service):

        result = self.health.check(
            service.url
        )

        return {
            "name": service.name,
            "slug": self._slug(
                service.name
            ),
            "container": getattr(
                service,
                "container",
                None,
            ),
            "port": service.port,
            "url": service.url,
            "healthy": result["healthy"],
            "status_code": result["status_code"],
            "response_time": result[
                "response_time"
            ],
        }

    def get_all(self):

        if not self.services:

            return []

        with ThreadPoolExecutor(
            max_workers=len(self.services)
        ) as executor:

            statuses = list(
                executor.map(
                    self._check,
                    self.services,
                )
            )

        return statuses

    def get(self, requested_slug):

        requested_slug = self._slug(
            requested_slug
        )

        for service in self.services:

            if (
                self._slug(service.name)
                == requested_slug
            ):

                return self._check(
                    service
                )

        return None