class RecommendationEngine:

    def build(self, results):

        recommendations = []

        for status, message in results:

            if "memory" in message.lower():

                recommendations.append(
                    "Close unused applications or investigate memory usage."
                )

            elif "cpu" in message.lower():

                recommendations.append(
                    "Investigate processes using high CPU."
                )

            elif "disk" in message.lower():

                recommendations.append(
                    "Clean unnecessary files or increase storage capacity."
                )

            elif "offline" in message.lower():

                service = message.replace(" is offline", "")

                recommendations.append(
                    f"Restart {service} and inspect its logs if the issue continues."
                )

            elif "unhealthy" in message.lower():

                service = message.replace(" is unhealthy", "")

                recommendations.append(
                    f"Open the {service} Web UI and review the Docker logs."
                )

        return recommendations