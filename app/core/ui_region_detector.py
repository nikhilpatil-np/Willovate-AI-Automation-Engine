import cv2
import json


def detect_regions(image_path):

    image = cv2.imread(image_path)

    if image is None:
        return {
            "success": False,
            "error": "Unable to read screenshot"
        }

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Threshold image
    _, threshold = cv2.threshold(
        blurred,
        200,
        255,
        cv2.THRESH_BINARY
    )

    # Find contours
    contours, _ = cv2.findContours(
        threshold,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )

    regions = []

    for contour in contours:

        x, y, width, height = cv2.boundingRect(contour)

        area = width * height

        # Ignore very small and very large regions
        if (
            width >= 40
            and height >= 20
            and area >= 800
            and area <= 100000
        ):

            regions.append({
                "x": x,
                "y": y,
                "width": width,
                "height": height
            })

    return {
        "success": True,
        "regions_detected": len(regions),
        "regions": regions
    }


if __name__ == "__main__":

    image_path = input("Enter screenshot path: ")

    result = detect_regions(image_path)

    print("\nUI Regions:\n")
    print(json.dumps(result, indent=4))