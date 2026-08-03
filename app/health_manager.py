import time
import requests


class HealthManager:

    def check(self, url):

        try:

            start = time.perf_counter()

            response = requests.get(
                url,
                timeout=3
            )

            elapsed = (
                time.perf_counter() - start
            ) * 1000

            return {
                "healthy": response.status_code < 400,
                "status_code": response.status_code,
                "response_time": round(elapsed, 1)
            }

        except requests.RequestException:

            return {
                "healthy": False,
                "status_code": None,
                "response_time": None
            }