import requests

response = requests.post(

    "http://127.0.0.1:8765/playback",

    json={

        "title": "The Matrix",

        "imdb_id": "tt0133093",

        "filename": "The.Matrix.1999.2160p.BluRay.mkv",

        "resolution": "3840x2160",

        "fps": 23.976,

        "hdr": True,

        "video_codec": "HEVC",

        "audio_codec": "DTS-HD MA",

        "audio_channels": "7.1",

    },

)

print(response.status_code)

print(response.text)