"""Main application file for the Hashtag Generator web app."""

import logging
import os
from datetime import datetime
from io import BytesIO

from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from google.cloud import storage
from werkzeug.utils import secure_filename
from ai import init_vertex_ai, get_image_hashtags

app = Flask(__name__)

# Load environment variables based on environment
if os.getenv("FLASK_ENV") == "production":
    LEVEL = logging.WARNING
    load_dotenv(".env")
else:
    LEVEL = logging.DEBUG
    load_dotenv(".env.dev")
app.logger.setLevel(LEVEL)
logging.basicConfig(level=LEVEL)

# Get App Version from environment
APP_VERSION = os.getenv("APP_VERSION", "1")

# Initialize Vertex AI
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
BUCKET_NAME = os.getenv("BUCKET_NAME")
if not GOOGLE_CLOUD_PROJECT:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
if not BUCKET_NAME:
    raise ValueError("BUCKET_NAME environment variable is required")

init_vertex_ai(GOOGLE_CLOUD_PROJECT)

# Initialize Google Cloud Storage client
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# Gemini's allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "heic", "heif"}


def allowed_file(filename):
    """
    Check if the given filename has an allowed extension.

    Args:
        filename (str): The name of the file to check.

    Returns:
        bool: True if the file has an allowed extension, False otherwise.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/hashtags", methods=["POST"])
def generate_hashtags():
    """
    Handle the generation of hashtags from an uploaded image file.

    This function processes a POST request containing an image file, saves the file to the server,
    and then attempts to generate hashtags based on the content of the image.

    Returns:
        Response: A JSON response containing either the generated hashtags or an error message.

    Possible JSON responses:
        - {'error': 'No file part'}: If the 'file' part is missing in the request.
        - {'error': 'No selected file'}: If no file is selected by the user.
        - {'error': 'File type not allowed'}: If the uploaded file type is not allowed.
        - {'hashtags': [list of hashtags]}: If the hashtags are successfully generated.
        - {'error': 'Error analyzing image: <error_message>'}: If there is an error during image analysis.

    HTTP Status Codes:
        - 400: Bad request, if the file part is missing, no file is selected, or the file type is not allowed.
        - 500: Internal server error, if there is an error during image analysis.
    """
    # Check if the post request has the file part
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]

    if "language" not in request.form:
        return jsonify({"error": "No language selected"}), 400
    language = request.form["language"]

    topic = None
    if "topic" in request.form:
        topic = request.form["topic"]

    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        try:
            # Create a unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_filename = secure_filename(file.filename)
            filename = f"{timestamp}_{original_filename}"

            # Save file to memory first
            file_content = file.read()
            file_obj = BytesIO(file_content)

            # Upload to Google Cloud Storage
            blob = bucket.blob(filename)
            blob.upload_from_file(file_obj, content_type=file.content_type)

            # Create a temporary file for AI processing
            temp_file = BytesIO(file_content)

            # Get hashtags from the image
            hashtags = get_image_hashtags(temp_file, language, topic)

            # Create and upload CSV file with hashtags
            csv_filename = filename.rsplit(".", 1)[0] + ".csv"
            csv_content = "hashtags, topic\n"
            topic = topic if topic else ""
            csv_content += " ".join(hashtags) + f", {topic}\n"
            csv_blob = bucket.blob(csv_filename)
            csv_blob.upload_from_string(csv_content, content_type="text/csv")

            return jsonify({"hashtags": hashtags})
        except Exception as e:
            app.logger.error(f"Error processing image: {str(e)}")
            return jsonify({"error": f"Error analyzing image: {str(e)}"}), 500

    return jsonify({"error": "File type not allowed"}), 400


@app.route("/")
def index():
    """
    Renders the index page.

    Returns:
        Response: The rendered HTML template for the index page.
    """
    return render_template("index.html")


@app.route("/privacy")
def privacy():
    """
    Renders the privacy policy page.

    Returns:
        Response: The rendered HTML template for the privacy policy page.
    """
    return render_template("privacy.html")


@app.route("/sw.js")
def sw():
    """
    Serve the service worker script.
    It needs to be served from the root directory to work properly.
    Ref: https://stackoverflow.com/a/48792264/2891324
    """

    with open(
        os.path.join(app.static_folder, "js", "sw.js"), "r", encoding="utf-8"
    ) as f:
        content = f.read()
        content = content.replace("{{APP_VERSION}}", APP_VERSION)
        return content, 200, {"Content-Type": "text/javascript"}
    return "", 404


@app.route("/.well-known/assetlinks.json")
def asset_links():
    """
    Server the assetlinks.json file for Android app linking.
    """

    with open(
        os.path.join(app.static_folder, "js", "assetlinks.json"), "r", encoding="utf-8"
    ) as f:
        content = f.read()
        return content, 200, {"Content-Type": "application/json"}
    return "", 404


if __name__ == "__main__":
    app.run(debug=True)
