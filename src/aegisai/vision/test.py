from google.cloud import vision

def detect_labels(image_path: str, key_path: str = "aegis-key.json"):
    client = vision.ImageAnnotatorClient.from_service_account_file(key_path)

    with open(image_path, "rb") as img_file:
        content = img_file.read()

    image = vision.Image(content=content)

    response = client.label_detection(image=image)
    labels = response.label_annotations

    result = []
    for label in labels:
        result.append({
            "description": label.description,
            "score": label.score,
        })

    return result