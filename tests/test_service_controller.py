from app.api.service_controller import ServiceController


print("=" * 60)
print("SERVICE CONTROLLER TEST")
print("=" * 60)
print()


commands = []


def successful_runner(command, timeout, cwd=None):

    commands.append(command)

    assert timeout == 60
    assert cwd is None

    return command[-1]


controller = ServiceController(
    command_runner=successful_runner,
    docker_command=lambda: "docker",
)

stop_result = controller.control(
    "stop",
    "example-service",
)

restart_result = controller.control(
    "restart",
    "example-service",
)

assert stop_result["ok"] is True
assert restart_result["ok"] is True
assert commands == [
    ["docker", "stop", "example-service"],
    ["docker", "restart", "example-service"],
]

print("✓ Stop and restart commands are constrained")

invalid_action = controller.control(
    "remove",
    "example-service",
)

invalid_container = controller.control(
    "stop",
    "../unsafe",
)

assert invalid_action["status"] == "invalid"
assert invalid_container["status"] == "invalid"
assert len(commands) == 2

print("✓ Invalid actions and container names rejected")


def failing_runner(command, timeout, cwd=None):

    raise RuntimeError("Docker unavailable")


failed_result = ServiceController(
    command_runner=failing_runner,
    docker_command=lambda: "docker",
).control(
    "restart",
    "example-service",
)

assert failed_result["ok"] is False
assert failed_result["status"] == "failed"
assert "Docker unavailable" in failed_result["message"]

print("✓ Docker failures reported safely")
print()
print("✓ Service controller test passed")
