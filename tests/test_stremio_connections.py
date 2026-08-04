import psutil

print("=" * 60)
print("STREMIO NETWORK CONNECTIONS")
print("=" * 60)
print()

for process in psutil.process_iter(["pid", "name"]):

    try:

        name = process.info["name"]

        if not name:
            continue

        if "stremio" not in name.lower():
            continue

        print(f"{name} ({process.pid})")
        print("-" * 60)

        connections = process.net_connections(kind="tcp")

        if not connections:
            print("No TCP connections.")
            print()
            continue

        for conn in connections:

            try:

                local = f"{conn.laddr.ip}:{conn.laddr.port}"

                if conn.raddr:
                    remote = f"{conn.raddr.ip}:{conn.raddr.port}"
                else:
                    remote = "-"

                print(
                    f"{local:<28} -> "
                    f"{remote:<28} "
                    f"{conn.status}"
                )

            except Exception:
                pass

        print()

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess,
    ):
        pass