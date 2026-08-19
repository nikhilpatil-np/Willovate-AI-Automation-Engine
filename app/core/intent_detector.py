class IntentDetector:

    def __init__(self):

        self.intent_keywords = {

            "ADD_CUSTOMER": [
                "add customer",
                "create customer",
                "new customer",
                "customer add",
                "customer create",
                "customer mein add",
                "customer me add",
                "customer ko add",
                "customer jodo",
                "customer jod",
                "customer bana",
                "customer banao",
                "customer banado",
                "ग्राहक जोड़",
                "employee add karo",
                "ग्राहक बनाओ"
            ],

            "UPDATE_PRODUCT": [
                "update product",
                "change product",
                "modify product",
                "product update",
                "product ka price",
                "product ki price",
                "price change",
                "price update",
                "product badlo",
                "product ki keemat"
            ],

            "DELETE_CUSTOMER": [
                "delete customer",
                "remove customer",
                "customer delete",
                "customer remove",
                "customer hatao",
                "customer hata",
                "ग्राहक हटाओ"
            ],

            "DOWNLOAD_REPORT": [
                "download report",
                "download the report",
                "export report",
                "report download",
                "report nikal",
                "report download karo",
                "रिपोर्ट डाउनलोड"
            ],

            "UPLOAD_FILE": [
                "upload file",
                "upload the file",
                "file upload",
                "file upload karo",
                "file chadhana",
                "फाइल अपलोड"
            ],

            "SEND_EMAIL": [
                "send email",
                "send mail",
                "email bhejo",
                "mail bhejo",
                "email karo",
                "mail karo",
                "ईमेल भेजो"
            ],

            "OPEN_PAGE": [
                "open",
                "open page",
                "go to",
                "open crm",
                "crm kholo",
                "page kholo",
                "page open karo",
                "खोलो"
            ],

            "FORM_FILL": [
                "fill form",
                "fill the form",
                "enter details",
                "form fill",
                "form bharo",
                "details bharo",
                "form bhar",
                "फॉर्म भरो"
            ],

            "TAKE_SCREENSHOT": [
                "take screenshot",
                "capture screenshot",
                "screenshot lo",
                "screenshot lena",
                "screenshot le",
                "स्क्रीनशॉट लो"
            ],

            "CHANGE_WEB": [
                "change logo",
                "update logo",
                "change header",
                "update header",
                "change color",
                "update color",
                "change background",
                "update background",
                "add banner",
                "add offer",
                "add announcement",
                "change title",
                "update title",
                "change text",
                "update text",
                "change button color",
                "update button",
                "change sidebar",
                "update sidebar color",
                "change theme",
                "logo change karo",
                "banner add karo",
                "offer add karo",
                "color change karo",
                "header badlo",
                "background badlo",
                "logo badlo",
                "website change karo",
                "webpage update karo",
                "site update karo",
                "वेबसाइट बदलो",
                "लोगो बदलो"
            ]
        }

    def detect_intent(self, text):

        text = text.lower().strip()

        # ---------------------------------
        # Check intents
        # ---------------------------------

        for intent, keywords in self.intent_keywords.items():

            for keyword in keywords:

                if keyword in text:

                    return intent

        return "UNKNOWN"


if __name__ == "__main__":

    detector = IntentDetector()

    print("\nEnglish / Hindi / Hinglish Intent Tester")
    print("-----------------------------------------")

    while True:

        sentence = input(
            "\nEnter instruction (type exit): "
        )

        if sentence.lower() == "exit":
            break

        intent = detector.detect_intent(
            sentence
        )

        print(
            "\nDetected Intent:",
            intent
        )