from app.technical.extractor import TechnicalExtractor


class TechnicalManager:

    def __init__(self):

        self.extractor = TechnicalExtractor()

    def analyse(self, context):

        #
        # Extract technical metadata.
        #
        context.technical = self.extractor.extract(context)

        return context