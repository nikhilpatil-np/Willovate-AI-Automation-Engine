import cv2
import os


def analyze_screenshot(image_path):
    """
    Load a screenshot and return basic image information.
    """

    if not os.path.exists(image_path):
        return {
            "success": False,
            "error": "Screenshot file not found"
        }

    image = cv2.imread(image_path)

    if image is None:
        return {
            "success": False,
            "error": "Unable to read screenshot"
        }

    height, width, channels = image.shape

    return {
        "success": True,
        "file": image_path,
        "width": width,
        "height": height,
        "channels": channels
    }


if __name__ == "__main__":

    image_path = input("Enter screenshot path: ")

    result = analyze_screenshot(image_path)

    print("\nScreenshot Analysis:\n")
    print(result)