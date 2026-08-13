import json

from ui_region_detector import detect_regions
from ui_region_classifier import classify_regions


def analyze_ui(image_path):

    detection = detect_regions(image_path)

    if not detection["success"]:
        return detection

    regions = detection["regions"]

    classified = classify_regions(regions)

    return {
        "success": True,
        "screenshot": image_path,
        "elements_detected": len(classified),
        "elements": classified
    }


if __name__ == "__main__":

    image_path = input("Enter screenshot path: ")

    result = analyze_ui(image_path)

    print("\nScreenshot UI Analysis:\n")
    print(json.dumps(result, indent=4))