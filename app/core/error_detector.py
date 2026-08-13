import json


ERROR_KEYWORDS = [
    "error",
    "failed",
    "failure",
    "invalid",
    "warning",
    "unable",
    "not found",
    "incorrect",
    "something went wrong"
]


def detect_error(text):
    """
    Detect common error messages from extracted screenshot text.
    """

    text_lower = text.lower()

    detected_errors = []

    for keyword in ERROR_KEYWORDS:
        if keyword in text_lower:
            detected_errors.append(keyword)

    return {
        "error_detected": len(detected_errors) > 0,
        "errors": detected_errors
    }


if __name__ == "__main__":

    test_messages = [
        "Customer added successfully.",
        "Error: Unable to save customer.",
        "Invalid phone number.",
        "Something went wrong."
    ]

    for message in test_messages:

        result = detect_error(message)

        print("\nMessage:", message)
        print(json.dumps(result, indent=4))