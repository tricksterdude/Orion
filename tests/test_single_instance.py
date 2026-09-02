import background
import main as main_module


print("=" * 60)
print("SINGLE INSTANCE TEST")
print("=" * 60)
print()


class FakeRuntime:

    created = 0
    run_calls = 0

    def __init__(self):

        self.__class__.created += 1

    def run(self):

        self.__class__.run_calls += 1


original_acquire = main_module.acquire_single_instance
original_release = main_module.release_single_instance
original_runtime = main_module.OrionRuntime

released = []

try:

    main_module.OrionRuntime = FakeRuntime
    main_module.acquire_single_instance = lambda: None
    main_module.release_single_instance = released.append

    main_module.main()

    assert FakeRuntime.created == 0
    assert released == []

    print("✓ Duplicate console runtime rejected")

    handle = object()
    main_module.acquire_single_instance = (
        lambda: handle
    )

    main_module.main()

    assert FakeRuntime.created == 1
    assert FakeRuntime.run_calls == 1
    assert released == [handle]

    print("✓ Single console runtime released cleanly")

    assert (
        background.acquire_single_instance.__module__
        == "app.single_instance"
    )

    print("✓ Background and console share one lock")

finally:

    main_module.acquire_single_instance = original_acquire
    main_module.release_single_instance = original_release
    main_module.OrionRuntime = original_runtime

print()
print("✓ Single instance test passed")
