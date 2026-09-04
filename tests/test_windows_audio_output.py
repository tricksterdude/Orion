from app.audio.windows_output import (
    AudioEndpoint,
    WindowsAudioOutput,
    WindowsAudioOutputError,
)


print("=" * 60)
print("WINDOWS AUDIO OUTPUT TEST")
print("=" * 60)
print()


endpoint = AudioEndpoint(
    name="Living room AVR",
    active=True,
    form_factor="HDMI/display audio",
)

assert endpoint.as_dict() == {
    "name": "Living room AVR",
    "active": True,
    "form_factor": "HDMI/display audio",
}

print("✓ Audio endpoint observations are serialisable")

assert WindowsAudioOutput.FORM_FACTORS[8] == "S/PDIF"
assert WindowsAudioOutput.FORM_FACTORS[9] == "HDMI/display audio"

print("✓ Windows endpoint form factors are mapped correctly")


try:

    WindowsAudioOutput(
        platform="linux"
    ).default_endpoint()

except WindowsAudioOutputError:

    pass

else:

    raise AssertionError(
        "Non-Windows audio observation should fail closed"
    )

print("✓ Unsupported platforms fail closed")
print()
print("✓ Windows audio output test passed")
