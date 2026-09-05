import copy


class OnboardingError(RuntimeError):
    pass


class OnboardingAssistant:

    PROVIDER_MARKERS = {
        "AIOStreams": ("aiostreams",),
        "UsenetStreamer": ("usenetstreamer",),
    }

    RECOMMENDED_SERVICE_MARKERS = (
        "aiostreams",
        "aiometadata",
        "usenetstreamer",
        "nzbdav",
    )

    def __init__(
        self,
        display,
        audio_output,
        stremio,
        service_discovery,
    ):

        self.display = display
        self.audio_output = audio_output
        self.stremio = stremio
        self.service_discovery = service_discovery

    @staticmethod
    def _service_text(service):

        return " ".join(
            str(service.get(field) or "")
            for field in (
                "name",
                "container",
                "image",
            )
        ).casefold()

    @classmethod
    def _recommended(cls, service):

        text = cls._service_text(service)

        return any(
            marker in text
            for marker in cls.RECOMMENDED_SERVICE_MARKERS
        )

    @classmethod
    def _providers(cls, services):

        detected = []

        for provider, markers in cls.PROVIDER_MARKERS.items():
            if any(
                any(
                    marker in cls._service_text(service)
                    for marker in markers
                )
                for service in services
            ):
                detected.append(provider)

        return detected

    @staticmethod
    def _area(identifier, name, ready, detail):

        return {
            "id": identifier,
            "name": name,
            "ready": bool(ready),
            "detail": detail,
        }

    def snapshot(
        self,
        profile,
        completed=False,
        playback_active=False,
    ):

        suggested = copy.deepcopy(profile)
        display = {
            "available": False,
            "resolution": None,
            "refresh": None,
            "message": "Display detection is unavailable.",
        }
        audio = {
            "available": False,
            "name": None,
            "form_factor": None,
            "message": "Audio output detection is unavailable.",
        }

        try:
            mode = self.display.current_mode()

            if mode is not None:
                display = {
                    "available": True,
                    "resolution": f"{mode.width}x{mode.height}",
                    "refresh": mode.refresh,
                    "message": (
                        f"{mode.width}x{mode.height} at "
                        f"{mode.refresh} Hz"
                    ),
                }

                if not completed and not playback_active:
                    suggested["media"]["display"][
                        "resolution"
                    ] = display["resolution"]
                    suggested["media"]["display"][
                        "desktop_refresh_rate"
                    ] = display["refresh"]

                if playback_active:
                    display["message"] += (
                        " (playback active; stored desktop "
                        "baseline preserved)"
                    )
        except Exception:
            pass

        try:
            endpoint = self.audio_output.default_endpoint()
            audio = {
                "available": bool(endpoint.active),
                "name": endpoint.name,
                "form_factor": endpoint.form_factor,
                "message": endpoint.name,
            }

            receiver = str(
                suggested["media"]["audio"].get(
                    "receiver"
                )
                or ""
            ).strip()

            if (
                not completed
                and endpoint.active
                and receiver.casefold()
                in {"", "not configured"}
            ):
                suggested["media"]["audio"][
                    "receiver"
                ] = endpoint.name
        except Exception:
            pass

        try:
            stremio = self.stremio.status()
        except Exception:
            stremio = {
                "state": "unavailable",
                "ready": False,
                "can_launch": False,
                "message": "Stremio detection is unavailable.",
            }

        try:
            discovery = self.service_discovery.discover(
                configured_services=profile["services"]
            )
        except Exception as error:
            discovery = {
                "candidates": [],
                "errors": [str(error)],
            }

        candidates = []

        for candidate in discovery.get("candidates", []):
            item = dict(candidate)
            item["recommended"] = self._recommended(item)
            candidates.append(item)

        provider_sources = (
            list(profile["services"])
            + [
                candidate
                for candidate in candidates
                if candidate["recommended"]
            ]
        )
        detected_providers = self._providers(provider_sources)

        if not completed and not suggested["providers"]:
            suggested["providers"] = detected_providers

        providers_ready = bool(suggested["providers"])
        services_ready = bool(
            profile["services"]
            or candidates
        )

        areas = [
            self._area(
                "display",
                "Display",
                display["available"],
                display["message"],
            ),
            self._area(
                "audio",
                "Audio output",
                audio["available"],
                audio["message"],
            ),
            self._area(
                "playback",
                "Playback",
                providers_ready,
                (
                    ", ".join(suggested["providers"])
                    if providers_ready
                    else stremio.get("message")
                ),
            ),
            self._area(
                "services",
                "Docker services",
                services_ready,
                (
                    f"{len(profile['services'])} configured"
                    if profile["services"]
                    else (
                        f"{len(candidates)} found"
                        if candidates
                        else "No published services found"
                    )
                ),
            ),
        ]

        return {
            "profile": suggested,
            "completed": bool(completed),
            "display": display,
            "audio": audio,
            "stremio": stremio,
            "areas": areas,
            "detected_count": sum(
                1 for area in areas if area["ready"]
            ),
            "area_count": len(areas),
            "discovered_services": candidates,
            "discovery_errors": list(
                discovery.get("errors", [])
            ),
            "detected_providers": detected_providers,
        }

    @staticmethod
    def _unique_name(base, port, used):

        clean = str(base or "Docker service").strip()
        clean = clean[:80]
        candidate = clean

        if candidate.casefold() not in used:
            return candidate

        suffix = f" {port}"
        candidate = clean[: 80 - len(suffix)] + suffix
        number = 2

        while candidate.casefold() in used:
            suffix = f" {port} ({number})"
            candidate = clean[: 80 - len(suffix)] + suffix
            number += 1

        return candidate

    def merge_services(self, configured_services, candidate_ids):

        configured = [
            dict(service)
            for service in configured_services
        ]
        selected = {
            str(candidate_id or "").strip()
            for candidate_id in candidate_ids
            if str(candidate_id or "").strip()
        }

        if not selected:
            return configured

        discovery = self.service_discovery.discover(
            configured_services=configured
        )
        available = {
            candidate["id"]: candidate
            for candidate in discovery.get("candidates", [])
        }
        missing = selected.difference(available)

        if missing:
            raise OnboardingError(
                "A selected Docker service is no longer available. "
                "Refresh setup and try again."
            )

        used_names = {
            str(service.get("name") or "").casefold()
            for service in configured
        }

        for candidate in discovery.get("candidates", []):
            if candidate["id"] not in selected:
                continue

            name = self._unique_name(
                candidate.get("name"),
                candidate.get("port"),
                used_names,
            )
            used_names.add(name.casefold())
            configured.append(
                {
                    "name": name,
                    "container": candidate["container"],
                    "port": candidate["port"],
                    "url": candidate["url"],
                }
            )

        return configured
