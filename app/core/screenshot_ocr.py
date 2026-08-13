import cv2
import pytesseract
import json

# Tesseract installation path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text(image_path):

    image = cv2.imread(image_path)

    if image is None:
        return {
            "success": False,
            "error": "Unable to read screenshot"
        }

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    text = pytesseract.image_to_string(gray)

    return {
        "success": True,
        "file": image_path,
        "text": text.strip()
    }


if __name__ == "__main__":

    image_path = input("Enter screenshot path: ")

    result = extract_text(image_path)

    print("\nExtracted Screenshot Text:\n")
    print(json.dumps(result, indent=4))