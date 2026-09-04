import json
import re
from fractions import Fraction


FFPROBE_ENTRIES = (
    "stream=codec_type,codec_name,codec_long_name,profile,"
    "width,height,r_frame_rate,avg_frame_rate,color_transfer,"
    "color_primaries,channels,channel_layout,sample_rate,bit_rate:"
    "stream_tags=title,handler_name:"
    "stream_disposition=default:"
    "stream_side_data=side_data_type:format=bit_rate"
)


def _positive_integer(value):

    try:

        number = int(value)

    except (TypeError, ValueError):

        return None

    return number if number > 0 else None


def parse_frame_rate(value):

    if not value or value == "0/0":

        return None

    try:

        return round(float(Fraction(value)), 3)

    except (TypeError, ValueError, ZeroDivisionError):

        return None


def _audio_markers(stream, filename):

    return (
        json.dumps(
            stream or {},
            ensure_ascii=False,
            sort_keys=True,
        )
        + " "
        + str(filename or "")
    ).casefold()


def _audio_label(stream, filename):

    if not stream:

        return None, None

    codec = str(stream.get("codec_name") or "").casefold()
    profile = str(stream.get("profile") or "").strip()
    markers = _audio_markers(stream, filename)

    if codec == "truehd":

        label = "Dolby TrueHD"

    elif codec == "eac3":

        label = "Dolby Digital Plus"

    elif codec == "ac3":

        label = "Dolby Digital"

    elif codec in {"dts", "dca"}:

        if any(
            marker in markers
            for marker in (
                "dts-hd ma",
                "dts-hd.ma",
                "dts hd ma",
                "master audio",
            )
        ):

            label = "DTS-HD Master Audio"

        elif "dts-hd" in markers or "dts hd" in markers:

            label = "DTS-HD"

        else:

            label = "DTS"

    elif codec.startswith("pcm_"):

        label = "PCM"

    elif codec:

        labels = {
            "aac": "AAC",
            "flac": "FLAC",
            "opus": "Opus",
            "vorbis": "Vorbis",
            "mp3": "MP3",
        }
        label = labels.get(codec, codec.upper())

    else:

        label = None

    immersive = None

    if (
        "atmos" in markers
        or re.search(r"\bjoc\b", markers)
    ):

        immersive = "Dolby Atmos"

    elif any(
        marker in markers
        for marker in (
            "dts:x",
            "dts-x",
            "dtsx",
        )
    ):

        immersive = "DTS:X"

    return label, immersive


def analyse_ffprobe_document(
    data,
    filename=None,
    source_host=None,
    url=None,
):

    streams = data.get("streams", [])

    video = next(
        (
            stream
            for stream in streams
            if stream.get("codec_type") == "video"
        ),
        None,
    )

    if video is None:

        raise RuntimeError("FFprobe found no video stream")

    audio_streams = [
        stream
        for stream in streams
        if stream.get("codec_type") == "audio"
    ]
    audio = next(
        (
            stream
            for stream in audio_streams
            if (stream.get("disposition") or {}).get("default")
        ),
        audio_streams[0] if audio_streams else None,
    )

    frame_rate = (
        video.get("avg_frame_rate")
        or video.get("r_frame_rate")
    )
    transfer = str(
        video.get("color_transfer") or ""
    ).casefold()
    filename_upper = str(filename or "").upper()
    dolby_vision = (
        ".DV." in filename_upper
        or "DOLBY.VISION" in filename_upper
    )
    hdr = transfer in {
        "smpte2084",
        "arib-std-b67",
    }

    audio_codec, immersive_audio = _audio_label(
        audio,
        filename,
    )

    channels = (
        str(audio.get("channel_layout") or "").strip()
        if audio
        else ""
    )

    if not channels and audio:

        count = _positive_integer(audio.get("channels"))

        if count:

            channels = f"{count} channels"

    format_data = data.get("format") or {}
    audio_profile = None

    if audio:

        audio_profile = (
            str(audio.get("profile") or "").strip()
            or None
        )

    return {
        "url": url,
        "filename": filename or None,
        "source_host": source_host,
        "fps": parse_frame_rate(frame_rate),
        "width": video.get("width"),
        "height": video.get("height"),
        "codec": video.get("codec_name"),
        "color_transfer": transfer,
        "color_primaries": video.get("color_primaries"),
        "hdr": hdr,
        "dolby_vision": dolby_vision,
        "audio_codec": audio_codec,
        "audio_profile": audio_profile,
        "audio_channels": channels or None,
        "audio_sample_rate": (
            _positive_integer(audio.get("sample_rate"))
            if audio
            else None
        ),
        "audio_bitrate": (
            _positive_integer(audio.get("bit_rate"))
            if audio
            else None
        ),
        "immersive_audio": immersive_audio,
        "bitrate": _positive_integer(
            format_data.get("bit_rate")
        ),
    }
