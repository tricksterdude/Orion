from app.runtime import OrionRuntime
from app.single_instance import (
    acquire_single_instance,
    release_single_instance,
)


def main():

    mutex = acquire_single_instance()

    if mutex is None:

        print(
            "Orion is already running; "
            "second launch cancelled."
        )
        return

    try:

        runtime = OrionRuntime()
        runtime.run()

    finally:

        release_single_instance(mutex)


if __name__ == "__main__":
    main()
