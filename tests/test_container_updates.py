from app.api.container_updates import (
    ContainerUpdateStatus,
)


print("=" * 60)
print("CONTAINER UPDATE STATUS TEST")
print("=" * 60)
print()


calls = []


def command_runner(command, timeout):

    calls.append(
        {
            "command": list(command),
            "timeout": timeout,
        }
    )

    image = command[3]

    if command[1:3] == [
        "image",
        "inspect",
    ]:

        if "aiostreams" in image:

            return (
                '["ghcr.io/viren070/'
                'aiostreams@sha256:'
                + ("a" * 64)
                + '"]'
            )

        return (
            '["gavpyro/'
            'usenetstreamer@sha256:'
            + ("c" * 64)
            + '"]'
        )

    if command[1:3] == [
        "buildx",
        "imagetools",
    ]:

        if "aiostreams" in image:

            digest = "b" * 64

        else:

            digest = "c" * 64

        return (
            f"Name: {image}\n"
            "MediaType: "
            "application/vnd.oci.image.index.v1+json\n"
            f"Digest:    sha256:{digest}\n"
        )

    raise AssertionError(
        f"Unexpected command: {command}"
    )


checker = ContainerUpdateStatus(
    command_runner=command_runner,
)

results = checker.get_all()

assert len(results) == 2

aiostreams = results[0]
usenetstreamer = results[1]

assert aiostreams["name"] == "AIOStreams"
assert aiostreams["status"] == "available"
assert aiostreams["update_available"] is True
assert aiostreams["message"] == "Update available."

print(
    "✓ AIOStreams update detected"
)

assert (
    usenetstreamer["name"]
    == "UsenetStreamer"
)

assert usenetstreamer["status"] == "current"
assert (
    usenetstreamer["update_available"]
    is False
)

assert usenetstreamer["message"] == "Up to date."

print(
    "✓ UsenetStreamer reported as current"
)

first_call_count = len(calls)

cached_results = checker.get_all()

assert cached_results == results
assert len(calls) == first_call_count

print(
    "✓ Registry checks cached safely"
)


def failing_runner(command, timeout):

    raise RuntimeError(
        "Registry unavailable"
    )


failure_checker = ContainerUpdateStatus(
    command_runner=failing_runner,
    cache_seconds=0,
)

failure_results = (
    failure_checker.get_all()
)

assert len(failure_results) == 2

assert all(
    item["status"] == "unable"
    for item in failure_results
)

assert all(
    item["update_available"] is None
    for item in failure_results
)

print(
    "✓ Registry failures handled safely"
)

print()
print(
    "✓ Container update status test passed"
)