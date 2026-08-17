import psutil

print("=" * 60)
print("STREMIO PROCESS INSPECTOR")
print("=" * 60)
print()

for process in psutil.process_iter(["pid", "name"]):

    try:

        name = process.info["name"]

        if not name:
            continue

        if "stremio" in name.lower():

            print(f"PID : {process.pid}")
            print(f"Name: {name}")

            children = process.children(recursive=True)

            if not children:

                print("Children: None")

            else:

                print()

                print("Child Processes")

                print("-" * 40)

                for child in children:

                    try:

                        print(
                            child.pid,
                            child.name()
                        )
                    except Exception:
                        pass

                print()

    except Exception:
        pass