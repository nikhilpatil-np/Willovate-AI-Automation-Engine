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
                "ग्राहक बनाओ"
            ],

            "ADD_EMPLOYEE": [
                "add employee",
                "create employee",
                "new employee",
                "employee add",
                "employee create",
                "register employee",
                "employee register",
                "employee jodo",
                "employee jod",
                "employee bana",
                "employee banao",
                "employee add karo",
                "naya employee",
                "कर्मचारी जोड़",
                "कर्मचारी बनाओ"
            ],

            "ADD_PRODUCT": [
                "add product",
                "create product",
                "new product",
                "product add",
                "product create",
                "insert product",
                "add a product",
                "add new product",
                "product jodo",
                "product jod",
                "naya product",
                "product banao",
                "product daalo",
                "उत्पाद जोड़ो",
                "नया उत्पाद"
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
                "ग्राहक हटाओ",
                "remove all customers",
                "delete all customers",
                "clear all customers",
                "saare customers hatao",
            ],

            "DELETE_PRODUCT": [
                "delete product",
                "remove product",
                "product delete",
                "product remove",
                "product hatao",
                "product hata",
                "remove all products",
                "delete all products",
                "clear all products",
                "saare products hatao",
                "products hatao",
            ],

            "DELETE_EMPLOYEE": [
                "delete employee",
                "remove employee",
                "employee delete",
                "employee remove",
                "employee hatao",
                "employee hata",
                "remove all employees",
                "delete all employees",
                "clear all employees",
                "saare employees hatao",
                "staff hatao",
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

            "ADD_OFFER": [
                "add offer",
                "add discount",
                "add sale",
                "add deal",
                "add promo",
                "add promotion",
                "add offer for",
                "add offer on",
                "offer add",
                "discount add",
                "sale add",
                "offer karo",
                "offer lagao",
                "sale lagao",
                "discount lagao",
                "offer dalo",
                "promo add",
                "add special offer",
                "add seasonal offer",
                "add flash sale",
            ],

            "CHANGE_WEB": [
                # Logo
                "change logo",
                "update logo",
                "change the logo",
                "update the logo",
                "set logo",
                "logo change",
                "logo update",
                # Header / topbar
                "change header",
                "update header",
                "set header",
                "change header color",
                "set header color",
                "change header background",
                "set header background",
                "update header background",
                "header color",
                "header background",
                # Color / background (generic)
                "change color",
                "update color",
                "set color",
                "change background",
                "update background",
                "set background",
                "change bg",
                "set bg",
                # Sidebar
                "change sidebar",
                "update sidebar",
                "set sidebar",
                "change sidebar color",
                "update sidebar color",
                "set sidebar color",
                "change sidebar background",
                "set sidebar background",
                "sidebar color",
                "sidebar background",
                # Theme
                "change theme",
                "update theme",
                "set theme",
                "dark mode",
                "light mode",
                # Banner / announcement
                "add banner",
                "add announcement",
                "add notice",
                "show banner",
                "create banner",
                # Title / text
                "change title",
                "update title",
                "set title",
                "change text",
                "update text",
                "set text",
                "change button color",
                "update button",
                "set button color",
                # Hindi / Hinglish
                "logo change karo",
                "banner add karo",
                "color change karo",
                "header badlo",
                "background badlo",
                "sidebar badlo",
                "logo badlo",
                "theme badlo",
                "website change karo",
                "webpage update karo",
                "site update karo",
                "rang badlo",
                "रंग बदलो",
                "वेबसाइट बदलो",
                "लोगो बदलो",
                "बैनर जोड़ो",
                "साइडबार का रंग"
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