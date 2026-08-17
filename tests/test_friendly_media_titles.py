from app.media.title import (
    friendly_media_title,
)


print("=" * 60)
print("FRIENDLY MEDIA TITLE TEST")
print("=" * 60)
print()

examples = {
    (
        "Minions.And.Monsters.2026."
        "2160p.iT.WEB-DL.DV.HDR10+."
        "MULTi-Ben.The.Men.mkv"
    ): "Minions And Monsters (2026)",

    (
        "The.Matrix.1999.2160p."
        "BluRay.HEVC.mkv"
    ): "The Matrix (1999)",

    (
        "Spider-Man.No.Way.Home.2021."
        "1080p.WEB-DL.mkv"
    ): "Spider-Man No Way Home (2021)",

    (
        "[YTS] The.Matrix.1999."
        "1080p.BluRay.mkv"
    ): "The Matrix (1999)",

    (
        "A.Movie.Without.A.Year."
        "2160p.WEB-DL.mkv"
    ): "A Movie Without A Year",
}

for filename, expected in examples.items():

    actual = friendly_media_title(
        filename
    )

    assert actual == expected, (
        f"Expected {expected!r}, "
        f"received {actual!r}"
    )

    print(
        f"✓ {actual}"
    )

assert friendly_media_title(None) is None
assert friendly_media_title("") is None

print()
print(
    "✓ Friendly media title test passed"
)