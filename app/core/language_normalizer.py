"""
Language Normalizer
===================
Normalizes English, Hindi (Devanagari), and Hinglish (romanized Hindi)
instructions into a clean English string that the rest of the pipeline
can process uniformly.

Responsibilities:
  1. Detect the dominant language of the input.
  2. Transliterate common Hinglish tokens to their English equivalents.
  3. Translate common Devanagari phrases to English.
  4. Fix common spelling mistakes found in the training dataset.
  5. Return a cleaned, lowercased English string.
"""

import re


# ---------------------------------------------------------------------------
# Devanagari (Hindi script) → English
# ---------------------------------------------------------------------------

DEVANAGARI_MAP = {
    # Customers
    "ग्राहक जोड़ो": "add customer",
    "ग्राहक जोड़ दो": "add customer",
    "ग्राहक बनाओ": "create customer",
    "ग्राहक हटाओ": "delete customer",
    "ग्राहक हटा दो": "delete customer",
    "ग्राहक अपडेट करो": "update customer",
    "कस्टमर जोड़ो": "add customer",
    "कस्टमर बनाओ": "create customer",
    "कस्टमर हटाओ": "delete customer",
    # Products
    "प्रोडक्ट का मूल्य बदलो": "change product price",
    "प्रोडक्ट अपडेट करो": "update product",
    # Files / Reports
    "फाइल अपलोड करो": "upload file",
    "फाइल अपलोड": "upload file",
    "रिपोर्ट डाउनलोड करो": "download report",
    "रिपोर्ट डाउनलोड": "download report",
    # Email
    "ईमेल भेजो": "send email",
    "ईमेल भेज दो": "send email",
    # Screenshot
    "स्क्रीनशॉट लो": "take screenshot",
    "स्क्रीनशॉट लेना": "take screenshot",
    # Save / Open
    "सेव करो": "save",
    "सेव": "save",
    "खोलो": "open",
    # Employee
    "कर्मचारी जोड़ो": "add employee",
    "कर्मचारी बनाओ": "create employee",
}


# ---------------------------------------------------------------------------
# Hinglish romanized tokens → English
# ---------------------------------------------------------------------------

HINGLISH_MAP = {
    # Add / Create
    "jodo": "add",
    "jod do": "add",
    "jod": "add",
    "banao": "create",
    "bana do": "create",
    "banado": "create",
    "bana": "create",
    "add karo": "add",
    "add kar do": "add",
    "add kardo": "add",
    # Update
    "update karo": "update",
    "update kar do": "update",
    "badlo": "update",
    "badal do": "update",
    # Delete / Remove
    "hatao": "delete",
    "hata do": "delete",
    "hata": "delete",
    "delete karo": "delete",
    "delete kar do": "delete",
    # Save
    "save karo": "save",
    "save kar do": "save",
    "save kardo": "save",
    # Open
    "kholo": "open",
    "khol do": "open",
    # Upload / Download
    "upload karo": "upload",
    "upload kar do": "upload",
    "download karo": "download",
    "download kar do": "download",
    # Send
    "bhejo": "send",
    "bhej do": "send",
    "email bhejo": "send email",
    "mail bhejo": "send email",
    # Navigate / Prepositions (noise words → remove)
    "naam ka": "named",
    "naam ki": "named",
    "naam ke": "named",
    "naam": "",
    "ko add karo": "add",
    "ko add kar do": "add",
    "mein add karo": "add",
    "me add karo": "add",
    "mein add kar do": "add",
    "me add kar do": "add",
    "customer mein": "customer",
    "customer me": "customer",
    "customer ko": "customer",
    "ke saath": "with",
    "ke sath": "with",
    "aur phir": "and then",
    "aur fir": "and then",
    "uske baad": "and then",
    "phir": "then",
    "fir": "then",
    # Misc verbs
    "dekho": "view",
    "dekhao": "show",
    "padho": "read",
    "karo": "",
    "kar do": "",
    "kardo": "",
}


# ---------------------------------------------------------------------------
# Spelling-mistake corrections
# ---------------------------------------------------------------------------

SPELLING_CORRECTIONS = {
    "costumer": "customer",
    "custmer": "customer",
    "cusomer": "customer",
    "cusotmer": "customer",
    "addd": "add",
    "adddd": "add",
    "creatte": "create",
    "creat": "create",
    "savee": "save",
    "saave": "save",
    "opeen": "open",
    "downlod": "download",
    "dowload": "download",
    "downlaod": "download",
    "uplaod": "upload",
    "uplod": "upload",
    "employe": "employee",
    "emploi": "employee",
    "employes": "employee",
    "emplyoee": "employee",
    "prodcut": "product",
    "porduct": "product",
    "prodct": "product",
    "prise": "price",
    "pric": "price",
    "eamil": "email",
    "emial": "email",
    "reprot": "report",
    "reprt": "report",
    "screensho": "screenshot",
    "screenshoot": "screenshot",
    "screnshort": "screenshot",
    "verifiy": "verify",
    "vrify": "verify",
}


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def detect_language(text: str) -> str:
    """
    Returns 'hi' for Devanagari-dominant text,
    'hinglish' for romanized Hindi, or 'en' for English.
    """

    devanagari_chars = re.findall(r"[\u0900-\u097F]", text)

    if len(devanagari_chars) > 3:
        return "hi"

    hinglish_tokens = [
        "karo", "kar do", "banao", "jodo", "hatao", "kholo",
        "bhejo", "phir", "uske baad", "naam", "mein", "mujhe",
        "aur", "ke saath", "dekho",
    ]

    text_lower = text.lower()

    for token in hinglish_tokens:
        if token in text_lower:
            return "hinglish"

    return "en"


# ---------------------------------------------------------------------------
# Core normalization
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """
    Normalize an English / Hindi / Hinglish instruction to a clean
    English string.

    Returns the normalized lowercase string.
    """

    if not text or not text.strip():
        return ""

    result = text.strip()

    # 1. Replace Devanagari phrases (longest match first)
    for hindi, english in sorted(DEVANAGARI_MAP.items(), key=lambda x: -len(x[0])):
        result = result.replace(hindi, english)

    result = result.lower()

    # 2. Replace Hinglish tokens (longest match first to avoid partial hits)
    for token, english in sorted(HINGLISH_MAP.items(), key=lambda x: -len(x[0])):
        result = result.replace(token, english)

    # 3. Fix spelling mistakes (word boundary aware)
    words = result.split()
    corrected = []
    for word in words:
        # Strip punctuation for lookup then restore
        stripped = re.sub(r"[^\w]", "", word)
        if stripped in SPELLING_CORRECTIONS:
            word = word.replace(stripped, SPELLING_CORRECTIONS[stripped])
        corrected.append(word)
    result = " ".join(corrected)

    # 4. Collapse multiple whitespace
    result = re.sub(r"\s{2,}", " ", result).strip()

    return result


def normalize_with_meta(text: str) -> dict:
    """
    Normalize and return metadata about the source language.

    Returns:
        {
            "original": str,
            "normalized": str,
            "detected_language": "en" | "hi" | "hinglish"
        }
    """

    lang = detect_language(text)
    normalized = normalize(text)

    return {
        "original": text,
        "normalized": normalized,
        "detected_language": lang,
    }


# ---------------------------------------------------------------------------
# Direct testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    import json

    test_cases = [
        # English
        "Add Rahul as customer with phone number 9876543210.",
        # Hinglish
        "Rahul naam ka customer jod do aur phir save karo.",
        "CRM kholo aur Pankaj ko add karo.",
        "Product ka price ₹599 kar do.",
        # Hindi (Devanagari)
        "ग्राहक जोड़ो",
        "फाइल अपलोड करो",
        # Spelling mistakes
        "Add a new costumer and save.",
        "Downlod the reprot.",
        "Create an employe named Rahul.",
    ]

    print("=" * 60)
    print("Language Normalizer Test")
    print("=" * 60)

    for tc in test_cases:
        result = normalize_with_meta(tc)
        print(f"\nOriginal  : {result['original']}")
        print(f"Language  : {result['detected_language']}")
        print(f"Normalized: {result['normalized']}")
