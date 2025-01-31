from pathlib import Path
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel, Part

from metaimage import image_coordinates


def init_vertex_ai(project_id: str, location: str = "us-central1"):
    """
    Initialize Vertex AI with the given project ID and location.

    Args:
        project_id (str): The Google Cloud project ID
        location (str): The location/region for Vertex AI services
    """
    aiplatform.init(project=project_id, location=location)


def get_image_hashtags(image_path: str | Path, language: str) -> list[str]:
    """
    Analyze an image using Vertex AI Gemini and generate relevant hashtags.

    Args:
        image_path (str | Path): Path to the image file
        language (str): The language to use for the generated hashtags

    Returns:
        list[str]: List of relevant hashtags
    """
    # Load and encode image
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found at {image_path}")

    # Enhance the prompt with location information if available
    location_prompt = " "
    try:
        coordinates = image_coordinates(image_path)
        if coordinates["city"] and coordinates["country"]:
            location_prompt = f"the image is taken in {coordinates['city']}, {coordinates['country']}."
        elif coordinates["country"]:
            location_prompt = f"the image is taken in {coordinates['country']}."
        elif coordinates["city"]:
            location_prompt = f"the image is taken in {coordinates['city']}."

        if location_prompt:
            location_prompt = (
                f"When generating the hashtags consider that {location_prompt}. "
            )
    except Exception as e:
        print(f"Error getting location information: {e}")

    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    # Initialize Gemini model
    model = GenerativeModel("gemini-1.5-flash")

    # Create the prompt parts
    prompt = [
        "Analyze this image and generate a list of relevant hashtags that describe its content, style, mood, and key elements. "
        "Return only the hashtags, separated by spaces, without any additional text. Each hashtag should start with #."
        + location_prompt
        + "Limit the number of hashtags to 20 and sort them by relevance."
        f"The language of the hashtag must be: {language} - international terms are allowed, if used in the context of the image.",
        Part.from_data(image_data, mime_type=f"image/{image_path.suffix[1:]}"),
    ]

    # Generate response
    response = model.generate_content(prompt)

    # Process response to extract hashtags
    hashtags_text = response.text.strip()
    # Split by spaces and ensure each tag starts with #
    hashtags = [
        tag if tag.startswith("#") else f"#{tag}"
        for tag in hashtags_text.split()
        if tag
    ]  # Filter out empty strings

    return hashtags
