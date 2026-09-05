import threading


class AudioGuidanceStatus:

    def __init__(self):

        self._lock = threading.Lock()
        self._result = self._inactive()

    @staticmethod
    def _inactive():

        return {
            "active": False,
            "state": "inactive",
            "title": None,
            "stream_audio": None,
            "expected_audio": None,
            "processor": None,
            "processor_installed": None,
            "output_name": None,
            "receiver_name": None,
            "receiver_mode": None,
            "receiver_input": None,
            "matches": None,
            "match_quality": None,
            "control_status": None,
            "automatic": False,
            "settled": False,
        }

    @staticmethod
    def _text(value, limit=200):

        text = str(value or "").strip()

        return text[:limit] or None

    def update(
        self,
        request,
        audio_output=None,
        processing=None,
        receiver=None,
        control=None,
        settled=False,
    ):

        audio_output = audio_output or {}
        processing = processing or {}
        receiver = receiver or {}
        control = control or {}

        expected = self._text(
            getattr(request, "immersive_audio", None)
        )
        matches = receiver.get(
            "matches_expected_audio"
        )
        match_quality = receiver.get("match_quality")

        if expected and not receiver.get("available"):

            state = "unavailable"

        elif expected and not settled:

            state = "checking"

        elif expected and match_quality == "compatible":

            state = "compatible"

        elif expected and matches is True:

            state = "matched"

        elif expected and matches is False:

            state = "mismatch"

        else:

            state = "observing"

        stream_audio = (
            self._text(
                getattr(request, "audio_profile", None)
            )
            or self._text(
                getattr(request, "audio_codec", None)
            )
        )

        result = {
            "active": True,
            "state": state,
            "title": self._text(
                getattr(request, "title", None)
            ),
            "stream_audio": stream_audio,
            "expected_audio": expected,
            "processor": self._text(
                processing.get("processor")
            ),
            "processor_installed": processing.get(
                "installed"
            ),
            "output_name": self._text(
                audio_output.get("name")
            ),
            "receiver_name": self._text(
                receiver.get("name")
            ),
            "receiver_mode": self._text(
                receiver.get("sound_mode")
            ),
            "receiver_input": self._text(
                receiver.get("selected_input")
            ),
            "matches": matches,
            "match_quality": match_quality,
            "control_status": self._text(
                control.get("status")
            ),
            "automatic": control.get("status") in {
                "current",
                "switched",
            },
            "settled": bool(settled),
        }

        with self._lock:

            self._result = result

        return dict(result)

    def clear(self):

        with self._lock:

            self._result = self._inactive()

    def recovery_failed(self):

        result = self._inactive()
        result.update(
            {
                "active": True,
                "state": "recovery_failed",
                "control_status": "failed",
                "automatic": True,
            }
        )

        with self._lock:

            self._result = result

        return dict(result)

    def get(self):

        with self._lock:

            return dict(self._result)


audio_guidance_status = AudioGuidanceStatus()
