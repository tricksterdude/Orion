import subprocess


class DockerManager:

    def get_running_containers(self):

        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return []

        return result.stdout.strip().splitlines()

    def is_running(self, container_name):

        return container_name in self.get_running_containers()