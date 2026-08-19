import threading


class RecoveryStatus:

    def __init__(self):

        self._lock = threading.Lock()
        self._result = {
            "status": "none",
            "message": None,
        }

    def set(self, result):

        if not isinstance(result, dict):

            result = {
                "status": "failed",
                "message": (
                    "Orion could not determine display "
                    "recovery status."
                ),
            }

        with self._lock:

            self._result = dict(result)

    def get(self):

        with self._lock:

            return dict(self._result)


display_recovery_status = RecoveryStatus()
