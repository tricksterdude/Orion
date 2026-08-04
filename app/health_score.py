class HealthScore:

    def calculate(self, results):

        score = 100

        for status, _ in results:

            if status == "WARNING":
                score -= 5

            elif status == "FAIL":
                score -= 15

        if score < 0:
            score = 0

        return score