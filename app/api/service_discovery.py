import json
import subprocess


class ContainerServiceDiscovery:

    def __init__(
        self,
        command_runner=None,
    ):

        self.command_runner = (
            command_runner
            or self._run_command
        )

    @staticmethod
    def _run_command(
        command,
        timeout,
        cwd=None,
    ):

        startupinfo = None
        creationflags = 0

        if hasattr(subprocess, "STARTUPINFO"):

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= (
                subprocess.STARTF_USESHOWWINDOW
            )

            creationflags = getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0,
            )

        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )

        if result.returncode != 0:

            message = (
                result.stderr.strip()
                or result.stdout.strip()
                or "Docker discovery failed."
            )

            raise RuntimeError(message)

        return result.stdout

    def _container_names(self):

        output = self.command_runner(
            [
                "docker",
                "container",
                "ls",
                "--all",
                "--format",
                "{{.Names}}",
            ],
            timeout=20,
            cwd=None,
        )

        return [
            line.strip()
            for line in output.splitlines()
            if line.strip()
        ]

    def _inspect(self, container_name):

        output = self.command_runner(
            [
                "docker",
                "inspect",
                container_name,
            ],
            timeout=20,
            cwd=None,
        )

        data = json.loads(output)

        if not data:

            raise RuntimeError(
                "Docker returned no container details."
            )

        return data[0]

    @staticmethod
    def _published_ports(details):

        network_settings = details.get(
            "NetworkSettings",
            {}
        )

        port_bindings = network_settings.get(
            "Ports",
            {}
        )

        published_ports = set()

        if not isinstance(
            port_bindings,
            dict,
        ):

            return []

        for bindings in port_bindings.values():

            if not isinstance(
                bindings,
                list,
            ):

                continue

            for binding in bindings:

                if not isinstance(
                    binding,
                    dict,
                ):

                    continue

                host_port = binding.get(
                    "HostPort"
                )

                try:

                    port = int(host_port)

                except (
                    TypeError,
                    ValueError,
                ):

                    continue

                if 1 <= port <= 65535:

                    published_ports.add(port)

        return sorted(published_ports)

    @staticmethod
    def _container_state(details):

        state = details.get(
            "State",
            {}
        )

        health = state.get("Health")

        health_status = None

        if isinstance(health, dict):

            health_status = health.get(
                "Status"
            )

        return {
            "running": bool(
                state.get("Running")
            ),
            "status": state.get(
                "Status",
                "unknown",
            ),
            "health": health_status,
        }

    def discover(
        self,
        configured_containers=None,
    ):

        configured = {
            str(container).lower()
            for container
            in (
                configured_containers
                or []
            )
            if container
        }

        candidates = []
        errors = []

        try:

            container_names = (
                self._container_names()
            )

        except Exception as error:

            return {
                "candidates": [],
                "errors": [str(error)],
            }

        for container_name in container_names:

            if (
                container_name.lower()
                in configured
            ):

                continue

            try:

                details = self._inspect(
                    container_name
                )

                ports = self._published_ports(
                    details
                )

                if not ports:

                    continue

                state = self._container_state(
                    details
                )

                image = (
                    details
                    .get("Config", {})
                    .get("Image")
                )

                for port in ports:

                    identifier = (
                        f"{container_name}-{port}"
                    )

                    candidates.append(
                        {
                            "id": identifier,
                            "name": container_name,
                            "container": (
                                container_name
                            ),
                            "image": image,
                            "port": port,
                            "url": (
                                "http://localhost:"
                                f"{port}"
                            ),
                            "running": (
                                state["running"]
                            ),
                            "status": (
                                state["status"]
                            ),
                            "health": (
                                state["health"]
                            ),
                        }
                    )

            except Exception as error:

                errors.append(
                    f"{container_name}: {error}"
                )

        candidates.sort(
            key=lambda item: (
                item["name"].lower(),
                item["port"],
            )
        )

        return {
            "candidates": candidates,
            "errors": errors,
        }

    def get_candidate(
        self,
        candidate_id,
        configured_containers=None,
    ):

        result = self.discover(
            configured_containers=(
                configured_containers
            )
        )

        for candidate in result["candidates"]:

            if candidate["id"] == candidate_id:

                return candidate

        return None
