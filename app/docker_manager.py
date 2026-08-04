import subprocess
import json


class DockerManager:

    def get_running_containers(self):

        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )

        return result.stdout.splitlines()

    def is_running(self, container):
        return container in self.get_running_containers()

    def inspect(self, container):

        result = subprocess.run(
            ["docker", "inspect", container],
            capture_output=True,
            text=True
        )

        return json.loads(result.stdout)[0]

    def restart(self, container):
        subprocess.run(["docker", "restart", container])

    def stop(self, container):
        subprocess.run(["docker", "stop", container])

    def start(self, container):
        subprocess.run(["docker", "start", container])

    def logs(self, container, lines=50):

        result = subprocess.run(
            ["docker", "logs", "--tail", str(lines), container],
            capture_output=True,
            text=True
        )

        return result.stdout

    def stats(self, container):

        result = subprocess.run(
            [
                "docker",
                "stats",
                "--no-stream",
                "--format",
                "{{.CPUPerc}}|{{.MemUsage}}",
                container
            ],
            capture_output=True,
            text=True
        )

        output = result.stdout.strip()

        if not output:
            return {
                "cpu": "Unknown",
                "memory": "Unknown"
            }

        cpu, memory = output.split("|")

        return {
            "cpu": cpu,
            "memory": memory
        }