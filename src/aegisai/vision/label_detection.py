from google.cloud import vision


def analyze_labels(image_path: str, key_path: str = "secrets/aegis-key.json"):
    """
    Analyze an image using Google Cloud Vision label detection.
    Uses the same service account as SafeSearch for consistency.
    """
    # Use the service account key (important!)
    client = vision.ImageAnnotatorClient.from_service_account_file(key_path)

    # Load the image
    with open(image_path, "rb") as f:
        content = f.read()

    image = vision.Image(content=content)

    # Request label detection
    response = client.label_detection(image=image)

    # Convert labels to a clean Python list
    labels = []
    for label in response.label_annotations:
        labels.append({
            "description": label.description,
            "score": label.score,
        })

    return labels
