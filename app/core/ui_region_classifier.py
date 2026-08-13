import json


def classify_region(region):

    width = region["width"]
    height = region["height"]

    # Wide region → possible table
    if width > 500 and height > 40:
        element_type = "TABLE"

    # Medium horizontal region → possible button/input
    elif 100 <= width <= 300 and 30 <= height <= 80:
        element_type = "BUTTON"

    # Small region
    elif width < 100 and height < 80:
        element_type = "INPUT"

    else:
        element_type = "UNKNOWN"

    return {
        "element_type": element_type,
        "region": region
    }


def classify_regions(regions):

    results = []

    for region in regions:
        results.append(
            classify_region(region)
        )

    return results


if __name__ == "__main__":

    test_regions = [
        {
            "x": 43,
            "y": 276,
            "width": 1154,
            "height": 52
        },
        {
            "x": 957,
            "y": 142,
            "width": 173,
            "height": 52
        },
        {
            "x": 547,
            "y": 75,
            "width": 40,
            "height": 33
        }
    ]

    result = classify_regions(test_regions)

    print("\nUI Region Classification:\n")
    print(json.dumps(result, indent=4))