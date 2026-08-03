class Diagnostics:

    def evaluate(self, service):

        if not service.running:

            return {
                "rating": "Offline",
                "recommendation": "Start the container."
            }

        if not service.healthy:

            return {
                "rating": "Unavailable",
                "recommendation": "Check the web service."
            }

        response = service.response_time

        if response < 50:

            return {
                "rating": "Excellent",
                "recommendation": "No action required."
            }

        if response < 150:

            return {
                "rating": "Good",
                "recommendation": "Operating normally."
            }

        if response < 500:

            return {
                "rating": "Slow",
                "recommendation": "Monitor performance."
            }

        return {
            "rating": "Warning",
            "recommendation": "Investigate service."
        }
