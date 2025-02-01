"""Module for interacting with Vertex AI services for image analysis."""

from io import BytesIO
import logging
from typing import Optional
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel, Part

import magic

from metaimage import image_coordinates

logger = logging.getLogger(__name__)


def init_vertex_ai(project_id: str, location: str = "us-central1"):
    """
    Initialize Vertex AI with the given project ID and location.

    Args:
        project_id (str): The Google Cloud project ID
        location (str): The location/region for Vertex AI services
    """
    aiplatform.init(project=project_id, location=location)


def get_image_hashtags(
    image_file: BytesIO, language: str, topic: Optional[str]
) -> list[str]:
    """
    Analyze an image using Vertex AI Gemini and generate relevant hashtags.

    Args:
        image_file (BytesIO): Image file as BytesIO object
        language (str): The language to use for the generated hashtags
        topic (str): Optional topic to provide additional context for the analysis

    Returns:
        list[str]: List of relevant hashtags
    """
    # Get image data
    image_data = image_file.getvalue()

    additional_prompt = ""
    try:
        coordinates = image_coordinates(image_data)
        if coordinates["city"] and coordinates["country"]:
            additional_prompt = f"the picture is taken in {coordinates['city']}, {coordinates['country']}."
        elif coordinates["country"]:
            additional_prompt = f"the picture is taken in {coordinates['country']}."
        elif coordinates["city"]:
            additional_prompt = f"the picture is taken in {coordinates['city']}."

        if additional_prompt:
            additional_prompt = (
                f"When generating the hashtags consider that {additional_prompt}. "
            )
    except Exception as e:
        logger.warning("Error getting location information: %s", str(e))

    # Initialize Gemini model
    model = GenerativeModel("gemini-1.5-flash")

    if topic:
        if additional_prompt:
            additional_prompt = f"{additional_prompt} The generated hashtags must be connected to the user-provided topic: {topic}."
        else:
            additional_prompt = f"The generated hashtags must be connected to the user-provided topic: {topic}."

    mime_type = magic.from_buffer(image_data, mime=True)

    # Create the prompt parts
    prompt = [
        "Analyze this image and generate a list of relevant hashtags that describe its content, style, mood, and key elements. "
        + additional_prompt
        + "Return only the hashtags, separated by spaces, without any additional text. Each hashtag should start with #."
        "Limit the number of hashtags to 20 and sort them by relevance."
        f"The language of the hashtag must be: {language} - international terms are allowed, if used in the context of the image.",
        Part.from_data(image_data, mime_type=mime_type),
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
    ]
    # Limit to 20 hashtags
    hashtags = hashtags[:20]

    return hashtags
