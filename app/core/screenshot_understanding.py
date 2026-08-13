import json

from screenshot_ocr import extract_text
from ui_region_detector import detect_regions
from ui_region_classifier import classify_regions
from error_detector import detect_error


def understand_screenshot(image_path):
    """
    Perform complete screenshot understanding.
    """

    # 1. OCR
    ocr_result = extract_text(image_path)

    if not ocr_result["success"]:
        return ocr_result

    extracted_text = ocr_result["text"]

    # 2. Detect UI regions
    region_result = detect_regions(image_path)

    if not region_result["success"]:
        return region_result

    regions = region_result["regions"]

    # 3. Classify UI regions
    classified_regions = classify_regions(regions)

    # 4. Detect errors
    error_result = detect_error(extracted_text)

    return {
        "success": True,
        "file": image_path,
        "ocr_text": extracted_text,
        "ui_regions": classified_regions,
        "error_detected": error_result["error_detected"],
        "errors": error_result["errors"]
    }


if __name__ == "__main__":

    image_path = input("Enter screenshot path: ")

    result = understand_screenshot(image_path)

    print("\nFinal Screenshot Understanding:\n")
    print(json.dumps(result, indent=4))