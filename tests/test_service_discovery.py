import json

from app.api.service_discovery import (
    ContainerServiceDiscovery,
)


print("=" * 60)
print("EXISTING SERVICE DISCOVERY TEST")
print("=" * 60)
print()


def inspect_document(
    name,
    image,
    ports,
    running=True,
    status="running",
    health=None,
):

    state = {
        "Running": running,
        "Status": status,
    }

    if health is not None:

        state["Health"] = {
            "Status": health,
        }

    return [
        {
            "Name": f"/{name}",
            "Config": {
                "Image": image,
            },
            "State": state,
            "NetworkSettings": {
                "Ports": ports,
            },
        }
    ]


documents = {
    "existing-service": inspect_document(
        "existing-service",
        "example/existing:latest",
        {
            "3000/tcp": [
                {
                    "HostIp": "0.0.0.0",
                    "HostPort": "3500",
                }
            ],
        },
        health="healthy",
    ),
    "candidate-service": inspect_document(
        "candidate-service",
        "example/candidate:latest",
        {
            "8080/tcp": [
                {
                    "HostIp": "0.0.0.0",
                    "HostPort": "8088",
                }
            ],
        },
        health="healthy",
    ),
    "stopped-service": inspect_document(
        "stopped-service",
        "example/stopped:latest",
        {
            "9000/tcp": [
                {
                    "HostIp": "127.0.0.1",
                    "HostPort": "9090",
                }
            ],
        },
        running=False,
        status="exited",
    ),
    "internal-redis": inspect_document(
        "internal-redis",
        "redis:latest",
        {
            "6379/tcp": None,
        },
    ),
}


def successful_command(
    command,
    timeout,
    cwd=None,
):

    assert timeout == 20
    assert cwd is None

    if command[:3] == [
        "docker",
        "container",
        "ls",
    ]:

        return (
            "existing-service\n"
            "candidate-service\n"
            "stopped-service\n"
            "internal-redis\n"
        )

    if command[:2] == [
        "docker",
        "inspect",
    ]:

        container = command[-1]

        return json.dumps(
            documents[container]
        )

    raise AssertionError(
        f"Unexpected command: {command}"
    )


discovery = ContainerServiceDiscovery(
    command_runner=successful_command
)

result = discovery.discover(
    configured_services=[
        {
            "container": "existing-service",
            "port": 3500,
        },
    ]
)

candidates = result["candidates"]
errors = result["errors"]

assert errors == []
assert len(candidates) == 2

candidate = next(
    item
    for item in candidates
    if item["container"] == "candidate-service"
)

assert candidate["id"] == "candidate-service-8088"
assert candidate["name"] == "candidate-service"
assert candidate["image"] == "example/candidate:latest"
assert candidate["port"] == 8088
assert candidate["url"] == "http://localhost:8088"
assert candidate["running"] is True
assert candidate["status"] == "running"
assert candidate["health"] == "healthy"

print("✓ Published Docker service discovered")

stopped = next(
    item
    for item in candidates
    if item["container"] == "stopped-service"
)

assert stopped["port"] == 9090
assert stopped["running"] is False
assert stopped["status"] == "exited"

print("✓ Stopped published service discovered")

assert all(
    item["container"] != "existing-service"
    for item in candidates
)

print("✓ Configured service excluded")

assert all(
    item["container"] != "internal-redis"
    for item in candidates
)

print("✓ Internal container without host port excluded")

selected = discovery.get_candidate(
    "candidate-service-8088",
    configured_services=[
        {
            "container": "existing-service",
            "port": 3500,
        },
    ],
)

assert selected is not None
assert selected["container"] == "candidate-service"
assert selected["port"] == 8088

missing = discovery.get_candidate(
    "missing-service-1234",
    configured_services=[
        {
            "container": "existing-service",
            "port": 3500,
        },
    ],
)

assert missing is None

print("✓ Candidate selected safely")


def failed_command(
    command,
    timeout,
    cwd=None,
):

    raise RuntimeError(
        "Docker is unavailable"
    )


failed_discovery = ContainerServiceDiscovery(
    command_runner=failed_command
)

failed_result = failed_discovery.discover()

assert failed_result["candidates"] == []
assert failed_result["errors"]
assert "Docker is unavailable" in (
    failed_result["errors"][0]
)

print("✓ Docker failures handled safely")

collision_documents = {
    "my_service": inspect_document(
        "my_service",
        "example/underscore:latest",
        {
            "8080/tcp": [
                {
                    "HostPort": "8080",
                }
            ],
        },
    ),
    "my-service": inspect_document(
        "my-service",
        "example/hyphen:latest",
        {
            "8080/tcp": [
                {
                    "HostPort": "8080",
                }
            ],
        },
    ),
}


def collision_runner(command, timeout, cwd=None):

    if command[1:3] == ["container", "ls"]:

        return "my_service\nmy-service\n"

    return json.dumps(
        collision_documents[command[-1]]
    )


collision_result = ContainerServiceDiscovery(
    command_runner=collision_runner
).discover()

assert {
    candidate["id"]
    for candidate in collision_result["candidates"]
} == {
    "my_service-8080",
    "my-service-8080",
}

print("✓ Similar Docker names keep unique identifiers")

multi_port_document = inspect_document(
    "multi-port-service",
    "example/multi-port:latest",
    {
        "8080/tcp": [
            {
                "HostPort": "8088",
            }
        ],
        "9090/tcp": [
            {
                "HostPort": "9099",
            }
        ],
    },
)


def multi_port_runner(command, timeout, cwd=None):

    if command[1:3] == ["container", "ls"]:

        return "multi-port-service\n"

    return json.dumps(multi_port_document)


multi_port_result = ContainerServiceDiscovery(
    command_runner=multi_port_runner
).discover(
    configured_services=[
        {
            "container": "multi-port-service",
            "port": 8088,
        }
    ]
)

assert [
    candidate["port"]
    for candidate
    in multi_port_result["candidates"]
] == [9099]

print("✓ Unconfigured port on configured container remains available")

print()
print("✓ Existing service discovery test passed")
