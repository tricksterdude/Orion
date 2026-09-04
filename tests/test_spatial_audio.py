from app.audio.spatial_processors import SpatialAudioProcessors


print("=" * 60)
print("SPATIAL AUDIO PROCESSOR TEST")
print("=" * 60)
print()


processors = SpatialAudioProcessors(
    package_names=[
        "DolbyLaboratories.DolbyAccess_3.25.0_x64",
        "DTSInc.DTSSoundUnbound_2026.1_x64",
    ]
)

assert processors.installed() == [
    {
        "id": "dolby_access",
        "name": "Dolby Access",
    },
    {
        "id": "dts_sound_unbound",
        "name": "DTS Sound Unbound",
    },
]

atmos = processors.recommendation("Dolby Atmos")
dtsx = processors.recommendation("DTS:X")
plain = processors.recommendation(None)

assert atmos["processor"] == "Dolby Access"
assert atmos["installed"] is True
assert atmos["control"] == "observe_only"
assert dtsx["processor"] == "DTS Sound Unbound"
assert dtsx["installed"] is True
assert plain["processor"] is None

print("✓ Dolby Access and DTS Sound Unbound detected")
print("✓ Content maps to the relevant optional processor")
print("✓ Processor control remains read-only")
print()
print("✓ Spatial audio processor test passed")
