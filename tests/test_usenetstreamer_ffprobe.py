import json
import re
import subprocess

from app.technical.nzbdav_probe import NZBDAVProbe


print("=" * 60)
print("USENETSTREAMER FFPROBE TEST")
print("=" * 60)
print()

logs = subprocess.run(
    [
        "docker",
        "logs",
        "--tail",
        "500",
        "usenetstreamer",
    ],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    check=True,
).stdout

matches = re.findall(
    r"Proxying GET "
    r"(http://host\.docker\.internal:8500/[^\r\n]+)",
    logs,
)

if not matches:

    raise RuntimeError(
        "No NZBDAV media URL found "
        "in UsenetStreamer logs."
    )

probe = NZBDAVProbe()

technical = probe.probe(
    matches[-1]
)

print(
    json.dumps(
        technical,
        indent=2,
    )
)