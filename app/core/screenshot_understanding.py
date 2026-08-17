"""
Screenshot Understanding
========================
Analyses a screenshot image to detect UI elements, extract text via OCR,
and identify error messages on the page.

This module fulfils Requirement 8 of the project brief:
  Use screenshots to detect buttons, input fields, dropdowns,
  tables, error messages and page structure.

Dependencies:
  pip install opencv-python pytesseract Pillow

Tesseract must be installed separately:
  Windows: https://github.com/UB-Mannheim/tesseract/wiki
  Set TESSERACT_PATH in this file if needed.
"""

import os
import re

# ---------------------------------------------------------------------------
# Optional imports — graceful fallback if libraries not installed
# ---------------------------------------------------------------------------

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
    # Uncomment and set path if Tesseract is not in system PATH:
    # pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
except ImportError:
    OCR_AVAILABLE = False


# ---------------------------------------------------------------------------
# Error keywords to scan for in OCR text
# ---------------------------------------------------------------------------

ERROR_KEYWORDS = [
    "error", "failed", "failure", "invalid", "warning",
    "unable", "not found", "incorrect", "something went wrong",
    "access denied", "timeout", "required",
]


# ---------------------------------------------------------------------------
# UI element classifier based on aspect ratio and area
# ---------------------------------------------------------------------------

def _classify_region(x: int, y: int, w: int, h: int, img_h: int) -> str:
    """Classify a detected contour region into a UI element type."""
    aspect = w / h if h > 0 else 0
    area   = w * h

    if aspect > 5 and h < 50:
        return "INPUT"         # wide and short → input field
    if 1.5 < aspect <= 5 and area < 15000:
        return "BUTTON"        # medium width button
    if aspect > 5 and h >= 50:
        return "TABLE"         # wide and taller → likely table row
    if area > 40000:
        return "TABLE"         # large area → table or container
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def extract_text_from_screenshot(image_path: str) -> str:
    """
    Extract all visible text from a screenshot using Tesseract OCR.

    Args:
        image_path: Path to the screenshot PNG/JPG file.

    Returns:
        Extracted text as a single string. Empty string if OCR unavailable.
    """
    if not OCR_AVAILABLE:
        return "(OCR not available — install pytesseract and Pillow)"

    if not os.path.isfile(image_path):
        return f"(File not found: {image_path})"

    try:
        img  = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as exc:
        return f"(OCR error: {exc})"


def detect_ui_regions(image_path: str) -> list:
    """
    Detect UI regions (buttons, inputs, tables) in a screenshot using OpenCV.

    Args:
        image_path: Path to the screenshot PNG/JPG file.

    Returns:
        List of dicts: [{type, x, y, width, height}, ...]
    """
    if not CV2_AVAILABLE:
        return [{"type": "UNKNOWN", "note": "opencv-python not installed"}]

    if not os.path.isfile(image_path):
        return []

    try:
        img    = cv2.imread(image_path)
        if img is None:
            return []

        gray   = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        edges  = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        regions = []
        h_img   = img.shape[0]

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w < 30 or h < 10:
                continue  # skip noise
            element_type = _classify_region(x, y, w, h, h_img)
            regions.append({
                "type":   element_type,
                "x":      x,
                "y":      y,
                "width":  w,
                "height": h,
            })

        return regions[:20]  # return top 20 regions

    except Exception as exc:
        return [{"type": "ERROR", "message": str(exc)}]


def detect_errors_in_screenshot(image_path: str) -> dict:
    """
    Check if a screenshot contains any error messages using OCR.

    Args:
        image_path: Path to the screenshot.

    Returns:
        {
            "error_detected": bool,
            "errors_found":   list[str],
            "ocr_text":       str,
        }
    """
    ocr_text   = extract_text_from_screenshot(image_path)
    text_lower = ocr_text.lower()

    # Only flag multi-word error phrases or words that appear as full words
    # to avoid false positives from HTML/CSS source text in OCR
    HIGH_CONFIDENCE_ERRORS = [
        "something went wrong",
        "access denied",
        "not found",
        "login failed",
        "invalid input",
        "required field",
        "server error",
        "connection failed",
        "unauthorized",
        "permission denied",
    ]

    errors_found = [kw for kw in HIGH_CONFIDENCE_ERRORS if kw in text_lower]

    return {
        "error_detected": len(errors_found) > 0,
        "errors_found":   errors_found,
        "ocr_text":       ocr_text,
    }


def understand_screenshot(image_path: str) -> dict:
    """
    Full screenshot understanding pipeline.

    Combines:
      1. OpenCV UI region detection
      2. Tesseract OCR text extraction
      3. Error keyword detection

    Args:
        image_path: Path to screenshot file.

    Returns:
        {
            "image_path":      str,
            "ui_regions":      list,
            "element_counts":  dict,
            "ocr_text":        str,
            "error_detected":  bool,
            "errors_found":    list,
            "page_structure":  str,
        }
    """
    ui_regions = detect_ui_regions(image_path)
    error_info = detect_errors_in_screenshot(image_path)

    # Count by type
    counts: dict = {}
    for r in ui_regions:
        t = r.get("type", "UNKNOWN")
        counts[t] = counts.get(t, 0) + 1

    # Simple page structure description
    structure_parts = []
    if counts.get("INPUT", 0) > 0:
        structure_parts.append(f"{counts['INPUT']} input field(s)")
    if counts.get("BUTTON", 0) > 0:
        structure_parts.append(f"{counts['BUTTON']} button(s)")
    if counts.get("TABLE", 0) > 0:
        structure_parts.append(f"{counts['TABLE']} table region(s)")
    page_structure = ", ".join(structure_parts) if structure_parts else "No elements detected"

    return {
        "image_path":     image_path,
        "ui_regions":     ui_regions,
        "element_counts": counts,
        "ocr_text":       error_info["ocr_text"],
        "error_detected": error_info["error_detected"],
        "errors_found":   error_info["errors_found"],
        "page_structure": page_structure,
    }


# ---------------------------------------------------------------------------
# Direct testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    import json

    # Use any existing screenshot from day7
    test_paths = [
        "screenshots/day7/test_page.png",
        "screenshots/day8/browser_automation.png",
        "screenshots/day8/verification.png",
    ]

    for path in test_paths:
        if os.path.isfile(path):
            print(f"\nAnalysing: {path}")
            result = understand_screenshot(path)
            print(json.dumps(result, indent=2))
            break
    else:
        print("No screenshot found for testing.")
        print("Place a PNG in screenshots/day7/ and run again.")
