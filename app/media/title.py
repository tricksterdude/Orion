import re
from pathlib import Path


YEAR_PATTERN = re.compile(
    r"(?<!\d)((?:19|20)\d{2})(?!\d)"
)

TECHNICAL_PATTERN = re.compile(
    r"\b(?:"
    r"480p|720p|1080p|2160p|4k|"
    r"uhd|bluray|web[- ]?dl|webrip|"
    r"remux|hdtv|dvdrip|"
    r"x264|x265|h264|h265|hevc"
    r")\b",
    re.IGNORECASE,
)

LEADING_TAG_PATTERN = re.compile(
    r"^(?:\[[^\]]+\]|\([^\)]+\))\s*"
)


def friendly_media_title(filename):

    if not filename:

        return None

    stem = Path(str(filename)).stem

    cleaned = re.sub(
        r"[._]+",
        " ",
        stem,
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    ).strip()

    cleaned = LEADING_TAG_PATTERN.sub(
        "",
        cleaned,
    ).strip()

    year = None
    title_text = cleaned

    year_match = YEAR_PATTERN.search(
        cleaned
    )

    if (
        year_match is not None
        and year_match.start() > 0
    ):

        year = year_match.group(1)

        title_text = cleaned[
            :year_match.start()
        ]

    else:

        technical_match = (
            TECHNICAL_PATTERN.search(
                cleaned
            )
        )

        if technical_match is not None:

            title_text = cleaned[
                :technical_match.start()
            ]

    title_text = title_text.strip(
        " -[]()"
    )

    if not title_text:

        return None

    title = title_text.title()

    if year is not None:

        return f"{title} ({year})"

    return title