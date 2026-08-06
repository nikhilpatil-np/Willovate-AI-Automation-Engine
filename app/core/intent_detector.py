class IntentDetector:

    def __init__(self):
        self.intent_keywords = {
            "ADD_CUSTOMER": ["add", "create", "new customer"],
            "UPDATE_PRODUCT": ["update", "change", "modify"],
            "DELETE_CUSTOMER": ["delete", "remove"],
            "DOWNLOAD_REPORT": ["download", "export"],
            "UPLOAD_FILE": ["upload"],
            "SEND_EMAIL": ["email", "send mail"],
            "OPEN_PAGE": ["open", "go to"],
            "FORM_FILL": ["fill", "enter"],
            "TAKE_SCREENSHOT": ["screenshot", "capture"]
        }

    def detect_intent(self, text):
        text = text.lower()

        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return intent

        return "UNKNOWN"


if __name__ == "__main__":
    detector = IntentDetector()

    sentence = input("Enter instruction: ")

    print(detector.detect_intent(sentence))