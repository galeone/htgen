"""Module for interacting with Vertex AI services for image analysis."""

from io import BytesIO
import logging
from typing import Optional
import os
import magic

from google import genai
from google.genai import types
from google.oauth2.service_account import Credentials

from metaimage import image_coordinates

logger = logging.getLogger(__name__)


class VertexAI:

    def __init__(self, project_id: str, location: str = "us-central1"):
        """
        Initialize Vertex AI with the given project ID and location.

        Args:
            project_id (str): The Google Cloud project ID
            location (str): The location/region for Vertex AI services
        """
        if not os.getenv("GOOGLE_CREDENTIALS_PATH"):
            raise ValueError("GOOGLE_CREDENTIALS_PATH environment variable is required")
        scopes = [
            "https://www.googleapis.com/auth/cloud-platform",
        ]
        credentials = Credentials.from_service_account_file(
            os.getenv("GOOGLE_CREDENTIALS_PATH"), scopes=scopes
        )
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
            credentials=credentials,
        )

    def get_image_hashtags(
        self, image_file: BytesIO, language: str, topic: Optional[str]
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

        model = "gemini-2.5-flash"

        if topic:
            if additional_prompt:
                additional_prompt = f"{additional_prompt} The generated hashtags must be connected to the user-provided topic: {topic}."
            else:
                additional_prompt = f"The generated hashtags must be connected to the user-provided topic: {topic}."

        # Create the prompt parts
        mime_type = magic.from_buffer(image_data, mime=True)
        prompt = [
            "Analyze this image and generate a list of relevant hashtags that describe its content, style, mood, and key elements. "
            + additional_prompt
            + "Return only the hashtags, separated by spaces, without any additional text. Each hashtag should start with #."
            "Limit the number of hashtags to 20 and sort them by relevance."
            f"The language of the hashtag must be: {language} - international terms are allowed, if used in the context of the image.",
            types.Part.from_bytes(data=image_data, mime_type=mime_type),
        ]

        # Generate response
        # Try to reduce all the safety settings to the minimum so we can avoid being blocked by the model
        # https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/configure-safety-filters
        safety_config = [
            types.SafetySetting(
                category="HARM_CATEGORY_UNSPECIFIED",
                threshold="BLOCK_ONLY_HIGH",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_ONLY_HIGH",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_ONLY_HIGH",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_ONLY_HIGH",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_ONLY_HIGH",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_CIVIC_INTEGRITY",
                threshold="BLOCK_ONLY_HIGH",
            ),
        ]

        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=safety_config,
            ),
        )

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
