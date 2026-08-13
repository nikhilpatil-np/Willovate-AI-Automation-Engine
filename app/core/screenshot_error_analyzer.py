import json

from screenshot_ocr import extract_text
from error_detector import detect_error


def analyze_screenshot_errors(image_path):

    ocr_result = extract_text(image_path)

    if not ocr_result["success"]:
        return ocr_result

    text = ocr_result["text"]

    error_result = detect_error(text)

    return {
        "success": True,
        "file": image_path,
        "extracted_text": text,
        "error_detected": error_result["error_detected"],
        "errors": error_result["errors"]
    }


if __name__ == "__main__":

    image_path = input("Enter screenshot path: ")

    result = analyze_screenshot_errors(image_path)

    print("\nScreenshot Error Analysis:\n")
    print(json.dumps(result, indent=4))