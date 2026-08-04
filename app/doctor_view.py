from ui.screen import Screen
from ui.progress import ProgressBar
from app.recommendation_engine import RecommendationEngine
from app.health_score import HealthScore


class DoctorView(Screen):

    def __init__(self):

        self.recommendations = RecommendationEngine()
        self.health_score = HealthScore()
        self.progress = ProgressBar()

    def show(self, results):

        self.title("ORION DOCTOR")

        score = self.health_score.calculate(results)

        if score >= 95:
            rating = "Excellent"

        elif score >= 80:
            rating = "Good"

        elif score >= 60:
            rating = "Warning"

        else:
            rating = "Critical"

        print(f"Health Score : {score}/100")
        print()

        print(self.progress.render(score) + f" {score}%")

        print()

        print(f"Status       : {rating}")

        print()

        passed = 0
        warnings = 0
        failed = 0

        for status, message in results:

            if status == "PASS":

                self.success(f"✓ {message}")
                passed += 1

            elif status == "WARNING":

                self.warning(f"⚠ {message}")
                warnings += 1

            else:

                self.error(f"✗ {message}")
                failed += 1

        print()

        self.title("SUMMARY")

        print(f"Passed   : {passed}")
        print(f"Warnings : {warnings}")
        print(f"Failed   : {failed}")

        print()

        if failed == 0 and warnings == 0:

            self.success("Overall Result : System Healthy")

        elif failed == 0:

            self.warning("Overall Result : Attention Recommended")

        else:

            self.error("Overall Result : Action Required")

        recommendations = self.recommendations.build(results)

        if recommendations:

            print()

            self.title("RECOMMENDATIONS")

            for recommendation in recommendations:

                print(f"• {recommendation}")

        print()

        self.wait()